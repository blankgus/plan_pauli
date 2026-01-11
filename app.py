# app_flexivel_com_edicao.py
from flask import Flask, render_template_string, request, jsonify, session, redirect
from datetime import datetime
import json
import os
import sqlite3

app = Flask(__name__)

# Configuração
app.config['SECRET_KEY'] = 'business_plan_escolar_flexivel_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'database_flexivel_edicao.db')

# Segmentos básicos (apenas para organização visual)
SEGMENTOS = {
    'ei': {
        'nome': 'Educação Infantil',
        'cor': '#FF6B8B',
        'descricao': '0-5 anos'
    },
    'ef_i': {
        'nome': 'Ensino Fundamental I',
        'cor': '#4ECDC4',
        'descricao': '6-10 anos'
    },
    'ef_ii': {
        'nome': 'Ensino Fundamental II',
        'cor': '#45B7D1',
        'descricao': '11-14 anos'
    },
    'em': {
        'nome': 'Ensino Médio',
        'cor': '#FF9F1C',
        'descricao': '15-17 anos'
    }
}

# Categorias de custos
CATEGORIAS_CUSTOS = {
    'investimento_inicial': [
        'Reforma de salas',
        'Compra de equipamentos',
        'Materiais permanentes',
        'Móveis e utensílios',
        'Licenças e legalização',
        'Projetos e consultorias'
    ],
    'custos_mensais_fixos': [
        'Aluguel do espaço',
        'Condomínio',
        'Água',
        'Energia elétrica',
        'Internet/Telefone',
        'Limpeza',
        'Seguro',
        'Manutenção'
    ],
    'custos_mensais_variaveis': [
        'Material de consumo',
        'Material didático',
        'Uniformes',
        'Transporte',
        'Alimentação',
        'Eventos e passeios'
    ],
    'marketing': [
        'Site e redes sociais',
        'Material impresso',
        'Publicidade online',
        'Divulgação local',
        'Feiras e eventos'
    ],
    'recursos_humanos': [
        'Salário professores',
        'Salário coordenador',
        'Salário secretária',
        'Salário auxiliar',
        'Encargos trabalhistas',
        'Benefícios',
        'Capacitação'
    ]
}

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            data_atualizacao TEXT,
            total_alunos INTEGER,
            total_participantes INTEGER,
            investimento_total REAL,
            custo_mensal_total REAL,
            receita_mensal_total REAL,
            lucro_mensal_total REAL,
            payback_meses REAL,
            roi_percentual REAL,
            dados_completos TEXT,
            editavel BOOLEAN DEFAULT 1
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS atividades_simulacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulacao_id INTEGER,
            segmento TEXT,
            nome_atividade TEXT,
            custo_hora_professor REAL,
            horas_semanais REAL,
            semanas_mes INTEGER DEFAULT 4,
            alunos INTEGER,
            nao_alunos INTEGER,
            receita_aluno REAL,
            receita_nao_aluno REAL,
            custo_material_mensal REAL,
            FOREIGN KEY (simulacao_id) REFERENCES simulacoes (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados com edição inicializado!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

def get_base_html(title="Business Plan Escolar com Edição", content=""):
    """Retorna o HTML base"""
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
    <style>
        :root {{
            --ei-color: #FF6B8B;
            --ef-i-color: #4ECDC4;
            --ef-ii-color: #45B7D1;
            --em-color: #FF9F1C;
        }}
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .card-header {{ border-radius: 10px 10px 0 0 !important; }}
        .btn-primary {{ background-color: #4361ee; border-color: #4361ee; }}
        .btn-primary:hover {{ background-color: #3a0ca3; border-color: #3a0ca3; }}
        .segmento-ei {{ border-left: 5px solid var(--ei-color) !important; }}
        .segmento-ef-i {{ border-left: 5px solid var(--ef-i-color) !important; }}
        .segmento-ef-ii {{ border-left: 5px solid var(--ef-ii-color) !important; }}
        .segmento-em {{ border-left: 5px solid var(--em-color) !important; }}
        .sticky-summary {{ position: sticky; top: 20px; }}
        .segmento-card {{ transition: transform 0.3s; }}
        .segmento-card:hover {{ transform: translateY(-5px); }}
        .chart-container {{ position: relative; height: 300px; width: 100%; }}
        .chart-container-lg {{ height: 400px; }}
        .atividade-row {{ 
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            position: relative;
        }}
        .remove-atividade {{
            color: #dc3545;
            cursor: pointer;
            font-size: 1.2em;
            position: absolute;
            top: 10px;
            right: 10px;
        }}
        .add-atividade {{
            background-color: #e9ecef;
            border: 2px dashed #6c757d;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .add-atividade:hover {{
            background-color: #d4edda;
            border-color: #28a745;
        }}
        .custo-calculado {{
            background-color: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .edit-badge {{
            position: absolute;
            top: 10px;
            right: 40px;
            font-size: 0.8em;
        }}
        .modal-lg-custom {{ max-width: 90%; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-edit"></i> Business Plan com Edição
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Início</a>
                <a class="nav-link" href="/simulacao"><i class="fas fa-plus-circle"></i> Nova</a>
                <a class="nav-link" href="/dashboard"><i class="fas fa-history"></i> Histórico</a>
                <a class="nav-link" href="/gerenciar"><i class="fas fa-cog"></i> Gerenciar</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {content}
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container text-center">
            <p>Sistema Completo de Business Plan Escolar - Crie, Edite, Analise</p>
            <p class="mb-0">© 2024 - Edite qualquer valor e recalcule automaticamente</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

@app.route('/')
def index():
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card bg-primary text-white">
                <div class="card-body py-5 text-center">
                    <h1 class="display-4 mb-4">
                        <i class="fas fa-school"></i> Business Plan com Edição Completa
                    </h1>
                    <p class="lead mb-4">
                        Crie, edite e analise simulações financeiras para atividades escolares
                    </p>
                    <div class="row mt-4">
                        <div class="col-md-3">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-edit fa-3x text-primary mb-3"></i>
                                    <h5>Edição Total</h5>
                                    <p>Edite qualquer valor</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-calculator fa-3x text-success mb-3"></i>
                                    <h5>Cálculos Reais</h5>
                                    <p>Baseado em horas e recursos</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-chart-pie fa-3x text-warning mb-3"></i>
                                    <h5>Gráficos</h5>
                                    <p>Visualização completa</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-database fa-3x text-info mb-3"></i>
                                    <h5>Histórico</h5>
                                    <p>Salve e edite depois</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/simulacao" class="btn btn-light btn-lg me-3">
                            <i class="fas fa-play-circle"></i> Nova Simulação
                        </a>
                        <a href="/dashboard" class="btn btn-outline-light btn-lg">
                            <i class="fas fa-history"></i> Ver Histórico
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan com Edição", content)

@app.route('/simulacao')
@app.route('/simulacao/<int:simulacao_id>')
def simulacao(simulacao_id=None):
    """Página de simulação - nova ou edição"""
    
    modo_edicao = simulacao_id is not None
    dados_edicao = {}
    
    if modo_edicao:
        # Carregar dados da simulação para edição
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (simulacao_id,))
            simulacao = cursor.fetchone()
            
            if simulacao:
                dados_completos = json.loads(simulacao['dados_completos'])
                dados_edicao = {
                    'id': simulacao_id,
                    'nome': simulacao['nome'],
                    'dados_entrada': dados_completos.get('entrada', {}),
                    'resultados': dados_completos.get('resultados', {}),
                    'atividades': dados_completos.get('atividades', []),
                    'custos': dados_completos.get('custos', {}),
                    'meses_analise': dados_completos.get('entrada', {}).get('meses_analise', 24)
                }
            
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar simulação para edição: {e}")
            return redirect('/dashboard')
    
    # Gerar HTML para os segmentos
    segmentos_html = ""
    for sigla, info in SEGMENTOS.items():
        segmentos_html += f'''
        <div class="col-md-6 mb-4">
            <div class="card segmento-card segmento-{sigla.replace('_', '-')}">
                <div class="card-header" style="background-color: {info['cor']}; color: white;">
                    <h5 class="mb-0"><i class="fas fa-graduation-cap"></i> {info['nome']}</h5>
                    <small class="opacity-75">{info['descricao']}</small>
                </div>
                <div class="card-body">
                    <div id="atividades_container_{sigla}" class="mb-3">
                        <!-- Atividades serão adicionadas aqui -->
                    </div>
                    
                    <div class="add-atividade mb-3" onclick="adicionarAtividade('{sigla}')">
                        <i class="fas fa-plus-circle fa-2x text-success mb-2"></i>
                        <p class="mb-0">Adicionar atividade</p>
                        <small class="text-muted">Clique para adicionar</small>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    # Gerar campos de custos
    campos_custos = ""
    categorias_detalhadas = {
        'investimento_inicial': ('info', 'Investimento Inicial'),
        'custos_mensais_fixos': ('warning', 'Custos Mensais Fixos'),
        'custos_mensais_variaveis': ('primary', 'Custos Variáveis'),
        'marketing': ('success', 'Marketing'),
        'recursos_humanos': ('danger', 'Recursos Humanos')
    }
    
    for categoria, (cor, titulo) in categorias_detalhadas.items():
        campos_custos += f'''
        <div class="col-md-6 mb-4">
            <div class="card">
                <div class="card-header bg-{cor} text-white">
                    <h5 class="mb-0"><i class="fas fa-{["tools", "dollar-sign", "shopping-cart", "bullhorn", "users"][list(categorias_detalhadas.keys()).index(categoria)]}"></i> {titulo}</h5>
                </div>
                <div class="card-body">
        '''
        
        for item in CATEGORIAS_CUSTOS[categoria]:
            campo_id = f"{categoria}_{item.replace(' ', '_').replace('/', '_').lower()}"
            is_mensal = 'mensais' in categoria
            
            # Buscar valor de edição se existir
            valor_edicao = 0
            if dados_edicao.get('custos', {}).get(categoria, {}).get(item, {}):
                valor_edicao = dados_edicao['custos'][categoria][item].get('valor', 0)
            
            campos_custos += f'''
            <div class="mb-3">
                <label class="form-label">{item}:</label>
                <div class="input-group">
                    <span class="input-group-text">R$</span>
                    <input type="number" class="form-control campo-custo" 
                           id="{campo_id}"
                           data-categoria="{categoria}"
                           data-item="{item}"
                           data-mensal="{str(is_mensal).lower()}"
                           value="{valor_edicao}"
                           min="0" 
                           step="10">
                    <span class="input-group-text">{'/mês' if is_mensal else ''}</span>
                </div>
            </div>
            '''
        
        campos_custos += '''
                </div>
            </div>
        </div>
        '''
    
    # Botão de ação específico
    botao_acao = "Calcular e Salvar"
    acao_js = "calcularSimulacao()"
    if modo_edicao:
        botao_acao = "Atualizar Simulação"
        acao_js = f"atualizarSimulacao({simulacao_id})"
    
    titulo_pagina = f"Editar Simulação #{simulacao_id}" if modo_edicao else "Nova Simulação"
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> {titulo_pagina}</h3>
                    {f'<p class="mb-0"><small>Editando simulação salva</small></p>' if modo_edicao else ''}
                </div>
                <div class="card-body">
                    <form id="simulacaoForm">
                        <!-- Configuração Geral -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-cog"></i> Configuração Geral
                                </h4>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Nome da Simulação:</label>
                                    <input type="text" class="form-control" id="nome_simulacao" 
                                           value="{dados_edicao.get('nome', 'Simulação ' + datetime.now().strftime('%d/%m/%Y'))}">
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meses para análise:</label>
                                    <select class="form-select" id="meses_analise">
                                        <option value="12" {'selected' if dados_edicao.get('meses_analise', 24) == 12 else ''}>12 meses</option>
                                        <option value="24" {'selected' if dados_edicao.get('meses_analise', 24) == 24 else ''}>24 meses</option>
                                        <option value="36" {'selected' if dados_edicao.get('meses_analise', 24) == 36 else ''}>36 meses</option>
                                        <option value="60" {'selected' if dados_edicao.get('meses_analise', 24) == 60 else ''}>60 meses</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Atividades -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-tasks"></i> Atividades por Segmento
                                </h4>
                                <p class="text-muted">Adicione atividades em cada segmento. Você pode digitar qualquer nome.</p>
                            </div>
                            
                            {segmentos_html}
                        </div>
                        
                        <!-- Custos -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-money-bill-wave"></i> Custos do Projeto
                                </h4>
                                <p class="text-muted">Preencha todos os custos relevantes.</p>
                                <div class="row">
                                    {campos_custos}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo e Ações -->
                        <div class="row">
                            <div class="col-md-5">
                                <div class="sticky-summary">
                                    <div class="card">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="fas fa-chart-line"></i> Resumo Financeiro</h5>
                                        </div>
                                        <div class="card-body">
                                            <div id="resumo_simulacao">
                                                <p class="text-center text-muted">Adicione atividades e custos</p>
                                            </div>
                                            
                                            <div class="mt-3">
                                                <button type="button" class="btn btn-primary w-100 mb-2" onclick="{acao_js}">
                                                    <i class="fas fa-save"></i> {botao_acao}
                                                </button>
                                                <button type="button" class="btn btn-outline-secondary w-100 mb-2" onclick="resetForm()">
                                                    <i class="fas fa-redo"></i> Limpar Tudo
                                                </button>
                                                {f'''
                                                <a href="/dashboard" class="btn btn-outline-warning w-100 mb-2">
                                                    <i class="fas fa-times"></i> Cancelar Edição
                                                </a>
                                                ''' if modo_edicao else '''
                                                <button type="button" class="btn btn-outline-info w-100" onclick="carregarExemplo()">
                                                    <i class="fas fa-magic"></i> Carregar Exemplo
                                                </button>
                                                '''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-7">
                                <div id="graficos_container">
                                    <!-- Gráficos aparecerão aqui -->
                                </div>
                                <div id="resultado_preview" style="display: none;">
                                    <!-- Resultado aparecerá aqui -->
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Template para uma atividade -->
    <template id="template-atividade">
        <div class="atividade-row">
            <i class="fas fa-times remove-atividade" onclick="removerAtividade(this)"></i>
            
            <div class="row">
                <div class="col-12">
                    <h6><i class="fas fa-dumbbell"></i> <span class="nome-atividade">Nova Atividade</span></h6>
                </div>
            </div>
            
            <div class="row g-2">
                <div class="col-md-6">
                    <div class="mb-2">
                        <label class="form-label small">Nome da Atividade:</label>
                        <input type="text" class="form-control form-control-sm nome-atividade-input" 
                               placeholder="Digite o nome..." value="Nova Atividade">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-2">
                        <label class="form-label small">Custo professor/hora (R$):</label>
                        <input type="number" class="form-control form-control-sm custo-hora" 
                               value="50" min="0" step="5">
                    </div>
                </div>
            </div>
            
            <div class="row g-2">
                <div class="col-md-4">
                    <div class="mb-2">
                        <label class="form-label small">Horas/semana:</label>
                        <input type="number" class="form-control form-control-sm horas-semanais" 
                               value="4" min="1" step="1">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-2">
                        <label class="form-label small">Semanas/mês:</label>
                        <input type="number" class="form-control form-control-sm semanas-mes" 
                               value="4" min="1" max="5" step="0.5">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="mb-2">
                        <label class="form-label small">Custo material/mês (R$):</label>
                        <input type="number" class="form-control form-control-sm custo-material" 
                               value="100" min="0" step="10">
                    </div>
                </div>
            </div>
            
            <div class="row g-2">
                <div class="col-md-3">
                    <div class="mb-2">
                        <label class="form-label small">Alunos:</label>
                        <input type="number" class="form-control form-control-sm alunos" 
                               value="10" min="0" step="1">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="mb-2">
                        <label class="form-label small">Não-alunos:</label>
                        <input type="number" class="form-control form-control-sm nao-alunos" 
                               value="5" min="0" step="1">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="mb-2">
                        <label class="form-label small">Receita aluno (R$/mês):</label>
                        <input type="number" class="form-control form-control-sm receita-aluno" 
                               value="150" min="0" step="10">
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="mb-2">
                        <label class="form-label small">Receita não-aluno (R$/mês):</label>
                        <input type="number" class="form-control form-control-sm receita-nao-aluno" 
                               value="200" min="0" step="10">
                    </div>
                </div>
            </div>
            
            <div class="custo-calculado">
                <div class="row small">
                    <div class="col-6">
                        <strong>Custo mensal:</strong><br>
                        <span class="custo-mensal-atividade">R$ 900,00</span>
                    </div>
                    <div class="col-6">
                        <strong>Receita mensal:</strong><br>
                        <span class="receita-mensal-atividade">R$ 2.500,00</span>
                    </div>
                </div>
            </div>
        </div>
    </template>

    <script>
    // Dados para carregar em edição
    const dadosEdicao = {json.dumps(dados_edicao.get('atividades', []))};
    
    document.addEventListener('DOMContentLoaded', function() {{
        // Configurar eventos
        document.getElementById('nome_simulacao').addEventListener('input', atualizarResumo);
        document.getElementById('meses_analise').addEventListener('change', atualizarResumo);
        
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            campo.addEventListener('input', atualizarResumo);
        }});
        
        // Se for edição, carregar atividades
        if (dadosEdicao.length > 0) {{
            carregarAtividadesEdicao();
        }} else {{
            // Adicionar uma atividade inicial em cada segmento
            Object.keys({json.dumps({seg: info['nome'] for seg, info in SEGMENTOS.items()})}).forEach(seg => {{
                adicionarAtividade(seg, true);
            }});
        }}
        
        // Inicializar
        setTimeout(atualizarResumo, 500);
    }});
    
    function carregarAtividadesEdicao() {{
        // Agrupar atividades por segmento
        const atividadesPorSegmento = {{}};
        
        dadosEdicao.forEach(atividade => {{
            const seg = atividade.segmento;
            if (!atividadesPorSegmento[seg]) {{
                atividadesPorSegmento[seg] = [];
            }}
            atividadesPorSegmento[seg].push(atividade);
        }});
        
        // Adicionar atividades em seus segmentos
        Object.entries(atividadesPorSegmento).forEach(([segmento, atividades]) => {{
            atividades.forEach(atividade => {{
                adicionarAtividadeComDados(segmento, atividade);
            }});
        }});
        
        // Se algum segmento ficou vazio, adicionar uma atividade vazia
        Object.keys({json.dumps({seg: info['nome'] for seg, info in SEGMENTOS.items()})}).forEach(seg => {{
            if (!atividadesPorSegmento[seg] || atividadesPorSegmento[seg].length === 0) {{
                adicionarAtividade(seg, true);
            }}
        }});
    }}
    
    function adicionarAtividadeComDados(segmento, dados) {{
        const container = document.getElementById(`atividades_container_${{segmento}}`);
        const template = document.getElementById('template-atividade').content.cloneNode(true);
        
        // Preencher com dados
        template.querySelector('.nome-atividade-input').value = dados.nome || 'Nova Atividade';
        template.querySelector('.nome-atividade').textContent = dados.nome || 'Nova Atividade';
        template.querySelector('.custo-hora').value = dados.custo_hora_professor || 50;
        template.querySelector('.horas-semanais').value = dados.horas_semanais || 4;
        template.querySelector('.semanas-mes').value = dados.semanas_mes || 4;
        template.querySelector('.custo-material').value = dados.custo_material_mensal || 100;
        template.querySelector('.alunos').value = dados.alunos || 10;
        template.querySelector('.nao-alunos').value = dados.nao_alunos || 5;
        template.querySelector('.receita-aluno').value = dados.receita_aluno || 150;
        template.querySelector('.receita-nao-aluno').value = dados.receita_nao_aluno || 200;
        
        container.appendChild(template);
        
        // Configurar eventos
        const atividadeRow = container.lastElementChild;
        const campos = atividadeRow.querySelectorAll('input');
        campos.forEach(campo => {{
            campo.addEventListener('input', function() {{
                if (campo.classList.contains('nome-atividade-input')) {{
                    const nomeAtividade = campo.closest('.atividade-row').querySelector('.nome-atividade');
                    nomeAtividade.textContent = campo.value || 'Nova Atividade';
                }}
                calcularAtividade(this.closest('.atividade-row'));
                atualizarResumo();
            }});
        }});
        
        calcularAtividade(atividadeRow);
    }}
    
    function adicionarAtividade(segmento, inicial = false) {{
        adicionarAtividadeComDados(segmento, {{}});
        if (!inicial) atualizarResumo();
    }}
    
    function removerAtividade(elemento) {{
        const atividadeRow = elemento.closest('.atividade-row');
        atividadeRow.remove();
        atualizarResumo();
    }}
    
    function calcularAtividade(atividadeRow) {{
        // Coletar valores
        const custoHora = parseFloat(atividadeRow.querySelector('.custo-hora').value) || 0;
        const horasSemanais = parseFloat(atividadeRow.querySelector('.horas-semanais').value) || 0;
        const semanasMes = parseFloat(atividadeRow.querySelector('.semanas-mes').value) || 4;
        const custoMaterial = parseFloat(atividadeRow.querySelector('.custo-material').value) || 0;
        const alunos = parseInt(atividadeRow.querySelector('.alunos').value) || 0;
        const naoAlunos = parseInt(atividadeRow.querySelector('.nao-alunos').value) || 0;
        const receitaAluno = parseFloat(atividadeRow.querySelector('.receita-aluno').value) || 0;
        const receitaNaoAluno = parseFloat(atividadeRow.querySelector('.receita-nao-aluno').value) || 0;
        
        // Calcular
        const custoProfessorMensal = custoHora * horasSemanais * semanasMes;
        const custoMensalTotal = custoProfessorMensal + custoMaterial;
        const receitaMensal = (alunos * receitaAluno) + (naoAlunos * receitaNaoAluno);
        
        // Atualizar display
        atividadeRow.querySelector('.custo-mensal-atividade').textContent = 
            `R$ ${{custoMensalTotal.toLocaleString('pt-BR')}}`;
        atividadeRow.querySelector('.receita-mensal-atividade').textContent = 
            `R$ ${{receitaMensal.toLocaleString('pt-BR')}}`;
        
        return {{
            custoMensal: custoMensalTotal,
            receitaMensal: receitaMensal,
            alunos: alunos,
            naoAlunos: naoAlunos
        }};
    }}
    
    function atualizarResumo() {{
        // Coletar todas as atividades
        let totalAlunos = 0;
        let totalNaoAlunos = 0;
        let receitaTotal = 0;
        let custoAtividadesTotal = 0;
        let totalAtividades = 0;
        
        const dadosSegmentos = {{}};
        
        // Percorrer segmentos
        Object.keys({json.dumps(SEGMENTOS)}).forEach(segmento => {{
            const container = document.getElementById(`atividades_container_${{segmento}}`);
            if (!container) return;
            
            const atividadesRows = container.querySelectorAll('.atividade-row');
            totalAtividades += atividadesRows.length;
            
            dadosSegmentos[segmento] = {{
                nome: {json.dumps({seg: info['nome'] for seg, info in SEGMENTOS.items()})}[segmento],
                atividades: [],
                receita: 0,
                custo: 0,
                participantes: 0,
                cor: {json.dumps({seg: info['cor'] for seg, info in SEGMENTOS.items()})}[segmento]
            }};
            
            atividadesRows.forEach(row => {{
                const dados = calcularAtividade(row);
                
                dadosSegmentos[segmento].atividades.push({{
                    nome: row.querySelector('.nome-atividade-input').value,
                    ...dados
                }});
                
                dadosSegmentos[segmento].receita += dados.receitaMensal;
                dadosSegmentos[segmento].custo += dados.custoMensal;
                dadosSegmentos[segmento].participantes += dados.alunos + dados.naoAlunos;
                
                totalAlunos += dados.alunos;
                totalNaoAlunos += dados.naoAlunos;
                receitaTotal += dados.receitaMensal;
                custoAtividadesTotal += dados.custoMensal;
            }});
        }});
        
        // Calcular custos gerais
        let investimentoTotal = 0;
        let custoMensalTotal = custoAtividadesTotal;
        
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            const valor = parseFloat(campo.value) || 0;
            const isMensal = campo.getAttribute('data-mensal') === 'true';
            
            if (isMensal) {{
                custoMensalTotal += valor;
            }} else {{
                investimentoTotal += valor;
            }}
        }});
        
        // Calcular indicadores
        const lucroMensal = receitaTotal - custoMensalTotal;
        const mesesAnalise = parseInt(document.getElementById('meses_analise').value) || 24;
        let paybackMeses = 0;
        let roiPercentual = 0;
        let retornoTotal = 0;
        
        if (lucroMensal > 0) {{
            retornoTotal = lucroMensal * mesesAnalise;
            if (investimentoTotal > 0) {{
                paybackMeses = investimentoTotal / lucroMensal;
                roiPercentual = (retornoTotal / investimentoTotal) * 100;
            }}
        }}
        
        // Atualizar resumo
        const resumoHTML = `
            <table class="table table-sm">
                <tr>
                    <td>Total de atividades:</td>
                    <td class="text-end"><span class="badge bg-primary">${{totalAtividades}}</span></td>
                </tr>
                <tr>
                    <td>Total de alunos:</td>
                    <td class="text-end"><strong>${{totalAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Total não-alunos:</td>
                    <td class="text-end"><strong>${{totalNaoAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Total participantes:</td>
                    <td class="text-end text-success"><strong>${{totalAlunos + totalNaoAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Receita atividades:</td>
                    <td class="text-end">R$ ${{receitaTotal.toLocaleString('pt-BR')}}</td>
                </tr>
                <tr>
                    <td>Custo atividades:</td>
                    <td class="text-end">R$ ${{custoAtividadesTotal.toLocaleString('pt-BR')}}</td>
                </tr>
                <tr>
                    <td>Investimento inicial:</td>
                    <td class="text-end">R$ ${{investimentoTotal.toLocaleString('pt-BR')}}</td>
                </tr>
                <tr>
                    <td>Custos gerais/mês:</td>
                    <td class="text-end">R$ ${{(custoMensalTotal - custoAtividadesTotal).toLocaleString('pt-BR')}}</td>
                </tr>
                <tr>
                    <td><strong>Custo total/mês:</strong></td>
                    <td class="text-end"><strong>R$ ${{custoMensalTotal.toLocaleString('pt-BR')}}</strong></td>
                </tr>
                <tr class="table-info">
                    <td><strong>Lucro Mensal:</strong></td>
                    <td class="text-end"><strong class="${{lucroMensal >= 0 ? 'text-success' : 'text-danger'}}">R$ ${{lucroMensal.toLocaleString('pt-BR')}}</strong></td>
                </tr>
                <tr>
                    <td>Payback estimado:</td>
                    <td class="text-end">${{paybackMeses > 0 ? paybackMeses.toFixed(1) + ' meses' : '---'}}</td>
                </tr>
                <tr>
                    <td>ROI (${{mesesAnalise}} meses):</td>
                    <td class="text-end"><span class="badge ${{roiPercentual > 100 ? 'bg-success' : roiPercentual > 50 ? 'bg-warning' : 'bg-danger'}}">${{roiPercentual > 0 ? roiPercentual.toFixed(1) + '%' : '---'}}</span></td>
                </tr>
            </table>
        `;
        
        document.getElementById('resumo_simulacao').innerHTML = resumoHTML;
        
        // Atualizar gráficos
        atualizarGraficos(dadosSegmentos);
    }}
    
    function atualizarGraficos(dadosSegmentos) {{
        const container = document.getElementById('graficos_container');
        
        const segmentosAtivos = Object.values(dadosSegmentos).filter(s => s.atividades.length > 0);
        
        if (segmentosAtivos.length === 0) {{
            container.innerHTML = '<div class="alert alert-info">Adicione atividades para ver os gráficos</div>';
            return;
        }}
        
        const labels = segmentosAtivos.map(s => s.nome.substring(0, 10) + '...');
        const cores = segmentosAtivos.map(s => s.cor);
        const receitas = segmentosAtivos.map(s => s.receita);
        const custos = segmentosAtivos.map(s => s.custo);
        const participantes = segmentosAtivos.map(s => s.participantes);
        
        const graficosHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-chart-bar"></i> Visualização em Tempo Real</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="chart-container">
                                <canvas id="chartReceita"></canvas>
                            </div>
                            <p class="text-center small">Receita por Segmento</p>
                        </div>
                        <div class="col-md-6">
                            <div class="chart-container">
                                <canvas id="chartParticipantes"></canvas>
                            </div>
                            <p class="text-center small">Participantes por Segmento</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = graficosHTML;
        
        // Criar gráficos
        setTimeout(() => {{
            // Gráfico de receita
            const ctx1 = document.getElementById('chartReceita').getContext('2d');
            if (window.chartReceita) window.chartReceita.destroy();
            window.chartReceita = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Receita (R$)',
                        data: receitas,
                        backgroundColor: cores,
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                callback: function(value) {{
                                    return 'R$ ' + value.toLocaleString('pt-BR');
                                }}
                            }}
                        }}
                    }}
                }}
            }});
            
            // Gráfico de participantes
            const ctx2 = document.getElementById('chartParticipantes').getContext('2d');
            if (window.chartParticipantes) window.chartParticipantes.destroy();
            window.chartParticipantes = new Chart(ctx2, {{
                type: 'doughnut',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: participantes,
                        backgroundColor: cores,
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ 
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}, 100);
    }}
    
    function resetForm() {{
        if (confirm('Limpar todos os dados?')) {{
            // Limpar atividades
            Object.keys({json.dumps(SEGMENTOS)}).forEach(seg => {{
                const container = document.getElementById(`atividades_container_${{seg}}`);
                if (container) container.innerHTML = '';
                adicionarAtividade(seg, true);
            }});
            
            // Limpar custos
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                campo.value = 0;
            }});
            
            // Limpar configurações
            document.getElementById('nome_simulacao').value = 'Simulação {datetime.now().strftime('%d/%m/%Y')}';
            document.getElementById('meses_analise').value = '24';
            
            atualizarResumo();
        }}
    }}
    
    function carregarExemplo() {{
        if (confirm('Carregar dados de exemplo?')) {{
            // Limpar primeiro
            Object.keys({json.dumps(SEGMENTOS)}).forEach(seg => {{
                const container = document.getElementById(`atividades_container_${{seg}}`);
                if (container) container.innerHTML = '';
            }});
            
            // Adicionar exemplos
            const exemplos = [
                {{ segmento: 'ei', nome: 'Música', custo_hora: 45, horas: 6, alunos: 15, nao_alunos: 5, receita_aluno: 120, receita_nao_aluno: 160, material: 200 }},
                {{ segmento: 'ef_i', nome: 'Futebol', custo_hora: 50, horas: 8, alunos: 20, nao_alunos: 10, receita_aluno: 80, receita_nao_aluno: 120, material: 300 }},
                {{ segmento: 'ef_ii', nome: 'Robótica', custo_hora: 60, horas: 6, alunos: 15, nao_alunos: 8, receita_aluno: 150, receita_nao_aluno: 200, material: 500 }},
                {{ segmento: 'em', nome: 'Preparatório ENEM', custo_hora: 70, horas: 12, alunos: 25, nao_alunos: 15, receita_aluno: 200, receita_nao_aluno: 280, material: 600 }}
            ];
            
            exemplos.forEach(exemplo => {{
                adicionarAtividadeComDados(exemplo.segmento, {{
                    nome: exemplo.nome,
                    custo_hora_professor: exemplo.custo_hora,
                    horas_semanais: exemplo.horas,
                    semanas_mes: 4,
                    custo_material_mensal: exemplo.material,
                    alunos: exemplo.alunos,
                    nao_alunos: exemplo.nao_alunos,
                    receita_aluno: exemplo.receita_aluno,
                    receita_nao_aluno: exemplo.receita_nao_aluno
                }});
            }});
            
            // Preencher custos exemplo
            const custosExemplo = {{
                'investimento_inicial_reforma_de_salas': 50000,
                'investimento_inicial_compra_de_equipamentos': 30000,
                'custos_mensais_fixos_aluguel_do_espaco': 8000,
                'custos_mensais_fixos_energia_eletrica': 1500,
                'recursos_humanos_salario_coordenador': 6000,
                'recursos_humanos_salario_secretaria': 3000
            }};
            
            Object.entries(custosExemplo).forEach(([id, valor]) => {{
                const campo = document.getElementById(id);
                if (campo) campo.value = valor;
            }});
            
            atualizarResumo();
        }}
    }}
    
    async function calcularSimulacao() {{
        await enviarSimulacao('/api/calcular_flexivel', 'POST');
    }}
    
    async function atualizarSimulacao(simulacaoId) {{
        await enviarSimulacao(`/api/atualizar_simulacao/${{simulacaoId}}`, 'PUT');
    }}
    
    async function enviarSimulacao(url, metodo) {{
        const btn = document.querySelector('button[onclick*="Simulacao"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        btn.disabled = true;
        
        try {{
            // Coletar dados
            const dados = {{
                nome: document.getElementById('nome_simulacao').value,
                meses_analise: parseInt(document.getElementById('meses_analise').value) || 24
            }};
            
            // Coletar atividades
            dados.atividades = [];
            Object.keys({json.dumps(SEGMENTOS)}).forEach(segmento => {{
                const container = document.getElementById(`atividades_container_${{segmento}}`);
                if (!container) return;
                
                const atividadesRows = container.querySelectorAll('.atividade-row');
                atividadesRows.forEach(row => {{
                    dados.atividades.push({{
                        segmento: segmento,
                        nome: row.querySelector('.nome-atividade-input').value,
                        custo_hora_professor: parseFloat(row.querySelector('.custo-hora').value) || 0,
                        horas_semanais: parseFloat(row.querySelector('.horas-semanais').value) || 0,
                        semanas_mes: parseFloat(row.querySelector('.semanas-mes').value) || 4,
                        custo_material_mensal: parseFloat(row.querySelector('.custo-material').value) || 0,
                        alunos: parseInt(row.querySelector('.alunos').value) || 0,
                        nao_alunos: parseInt(row.querySelector('.nao-alunos').value) || 0,
                        receita_aluno: parseFloat(row.querySelector('.receita-aluno').value) || 0,
                        receita_nao_aluno: parseFloat(row.querySelector('.receita-nao-aluno').value) || 0
                    }});
                }});
            }});
            
            // Coletar custos
            dados.custos = {{}};
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                const categoria = campo.getAttribute('data-categoria');
                const item = campo.getAttribute('data-item');
                const valor = parseFloat(campo.value) || 0;
                const isMensal = campo.getAttribute('data-mensal') === 'true';
                
                if (!dados.custos[categoria]) {{
                    dados.custos[categoria] = {{}};
                }}
                dados.custos[categoria][item] = {{
                    valor: valor,
                    mensal: isMensal
                }};
            }});
            
            // Enviar
            const response = await fetch(url, {{
                method: metodo,
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(dados)
            }});
            
            if (!response.ok) {{
                const error = await response.text();
                throw new Error(`Erro ${{response.status}}: ${{error}}`);
            }}
            
            const resultados = await response.json();
            
            // Mostrar sucesso
            document.getElementById('resultado_preview').innerHTML = `
                <div class="alert alert-success mt-3">
                    <h5><i class="fas fa-check-circle"></i> Simulação salva!</h5>
                    <p>Redirecionando para resultados...</p>
                </div>
            `;
            document.getElementById('resultado_preview').style.display = 'block';
            
            setTimeout(() => {{
                window.location.href = '/resultado_flexivel';
            }}, 2000);
            
        }} catch (error) {{
            console.error('Erro:', error);
            alert('Erro: ' + error.message);
        }} finally {{
            btn.innerHTML = originalText;
            btn.disabled = false;
        }}
    }}
    </script>
    '''
    return get_base_html(titulo_pagina, content)

@app.route('/api/calcular_flexivel', methods=['POST'])
def api_calcular_flexivel():
    """API para nova simulação"""
    return processar_simulacao(request)

@app.route('/api/atualizar_simulacao/<int:simulacao_id>', methods=['PUT'])
def api_atualizar_simulacao(simulacao_id):
    """API para atualizar simulação"""
    return processar_simulacao(request, simulacao_id)

def processar_simulacao(request_obj, simulacao_id=None):
    """Processa simulação (nova ou atualização)"""
    try:
        dados = request_obj.get_json()
        if not dados:
            return jsonify({'error': 'Nenhum dado recebido'}), 400
        
        print(f"Processando simulação {'#{}'.format(simulacao_id) if simulacao_id else 'nova'}")
        
        # Calcular totais
        totais = {
            'total_alunos': 0,
            'total_nao_alunos': 0,
            'total_participantes': 0,
            'receita_mensal_atividades': 0,
            'custo_mensal_atividades': 0,
            'investimento_inicial': 0,
            'custo_mensal_geral': 0,
            'lucro_mensal': 0
        }
        
        # Processar atividades
        atividades_detalhadas = []
        for atividade in dados.get('atividades', []):
            # Cálculos
            custo_professor_mensal = (atividade['custo_hora_professor'] * 
                                     atividade['horas_semanais'] * 
                                     atividade['semanas_mes'])
            custo_total_atividade = custo_professor_mensal + atividade['custo_material_mensal']
            receita_atividade = ((atividade['alunos'] * atividade['receita_aluno']) + 
                                (atividade['nao_alunos'] * atividade['receita_nao_aluno']))
            
            # Atualizar totais
            totais['total_alunos'] += atividade['alunos']
            totais['total_nao_alunos'] += atividade['nao_alunos']
            totais['total_participantes'] += (atividade['alunos'] + atividade['nao_alunos'])
            totais['receita_mensal_atividades'] += receita_atividade
            totais['custo_mensal_atividades'] += custo_total_atividade
            
            # Detalhes
            atividades_detalhadas.append({
                **atividade,
                'custo_professor_mensal': custo_professor_mensal,
                'custo_total_mensal': custo_total_atividade,
                'receita_mensal': receita_atividade,
                'lucro_mensal': receita_atividade - custo_total_atividade
            })
        
        # Processar custos
        custos_detalhados = dados.get('custos', {})
        for categoria, itens in custos_detalhados.items():
            for item, info in itens.items():
                valor = info.get('valor', 0)
                if info.get('mensal'):
                    totais['custo_mensal_geral'] += valor
                else:
                    totais['investimento_inicial'] += valor
        
        # Totais finais
        totais['custo_mensal_total'] = totais['custo_mensal_atividades'] + totais['custo_mensal_geral']
        totais['lucro_mensal'] = totais['receita_mensal_atividades'] - totais['custo_mensal_total']
        
        # Indicadores
        meses_analise = dados.get('meses_analise', 24)
        payback_meses = 0
        roi_percentual = 0
        retorno_total = 0
        
        if totais['lucro_mensal'] > 0:
            retorno_total = totais['lucro_mensal'] * meses_analise
            if totais['investimento_inicial'] > 0:
                payback_meses = totais['investimento_inicial'] / totais['lucro_mensal']
                roi_percentual = (retorno_total / totais['investimento_inicial']) * 100
        
        # Resultados
        resultados = {
            **totais,
            'payback_meses': payback_meses,
            'roi_percentual': roi_percentual,
            'retorno_total': retorno_total,
            'meses_analise': meses_analise,
            'total_atividades': len(atividades_detalhadas)
        }
        
        print(f"Calculado: {len(atividades_detalhadas)} atividades, Lucro: R$ {totais['lucro_mensal']:,.2f}")
        
        # Salvar na sessão
        session['ultima_simulacao_flexivel'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'atividades_detalhadas': atividades_detalhadas,
            'custos_detalhados': custos_detalhados,
            'nome_simulacao': dados.get('nome', 'Simulação')
        }
        
        # Salvar/Atualizar no banco
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            if simulacao_id:
                # Atualizar
                cursor.execute('''
                UPDATE simulacoes SET
                    nome = ?,
                    data_atualizacao = ?,
                    total_alunos = ?,
                    total_participantes = ?,
                    investimento_total = ?,
                    custo_mensal_total = ?,
                    receita_mensal_total = ?,
                    lucro_mensal_total = ?,
                    payback_meses = ?,
                    roi_percentual = ?,
                    dados_completos = ?
                WHERE id = ?
                ''', (
                    dados.get('nome', f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    totais['total_alunos'],
                    totais['total_participantes'],
                    totais['investimento_inicial'],
                    totais['custo_mensal_total'],
                    totais['receita_mensal_atividades'],
                    totais['lucro_mensal'],
                    payback_meses,
                    roi_percentual,
                    json.dumps({
                        'entrada': dados,
                        'resultados': resultados,
                        'atividades': atividades_detalhadas,
                        'custos': custos_detalhados
                    }),
                    simulacao_id
                ))
                
                # Remover atividades antigas
                cursor.execute('DELETE FROM atividades_simulacao WHERE simulacao_id = ?', (simulacao_id,))
                
                print(f"✅ Simulação #{simulacao_id} atualizada!")
            else:
                # Nova
                cursor.execute('''
                INSERT INTO simulacoes (
                    nome, data_criacao, data_atualizacao, total_alunos, total_participantes,
                    investimento_total, custo_mensal_total, receita_mensal_total,
                    lucro_mensal_total, payback_meses, roi_percentual, dados_completos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dados.get('nome', f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    totais['total_alunos'],
                    totais['total_participantes'],
                    totais['investimento_inicial'],
                    totais['custo_mensal_total'],
                    totais['receita_mensal_atividades'],
                    totais['lucro_mensal'],
                    payback_meses,
                    roi_percentual,
                    json.dumps({
                        'entrada': dados,
                        'resultados': resultados,
                        'atividades': atividades_detalhadas,
                        'custos': custos_detalhados
                    })
                ))
                
                simulacao_id = cursor.lastrowid
                print(f"✅ Nova simulação #{simulacao_id} criada!")
            
            # Salvar atividades
            for atividade in atividades_detalhadas:
                cursor.execute('''
                INSERT INTO atividades_simulacao (
                    simulacao_id, segmento, nome_atividade, custo_hora_professor,
                    horas_semanais, semanas_mes, alunos, nao_alunos,
                    receita_aluno, receita_nao_aluno, custo_material_mensal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    simulacao_id,
                    atividade['segmento'],
                    atividade['nome'],
                    atividade['custo_hora_professor'],
                    atividade['horas_semanais'],
                    atividade['semanas_mes'],
                    atividade['alunos'],
                    atividade['nao_alunos'],
                    atividade['receita_aluno'],
                    atividade['receita_nao_aluno'],
                    atividade['custo_material_mensal']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Erro no banco: {e}")
        
        return jsonify(resultados)
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Erro interno'
        }), 500

@app.route('/resultado_flexivel')
def resultado_flexivel():
    """Página de resultados"""
    if 'ultima_simulacao_flexivel' not in session:
        return redirect('/simulacao')
    
    dados = session['ultima_simulacao_flexivel']
    resultados = dados['resultados']
    atividades = dados['atividades_detalhadas']
    nome_simulacao = dados.get('nome_simulacao', 'Simulação')
    
    # Agrupar por segmento
    atividades_por_segmento = {}
    for atividade in atividades:
        seg = atividade['segmento']
        if seg not in atividades_por_segmento:
            atividades_por_segmento[seg] = []
        atividades_por_segmento[seg].append(atividade)
    
    # HTML para tabela de atividades
    tabela_atividades = ""
    for seg, ativs in atividades_por_segmento.items():
        for a in ativs:
            tabela_atividades += f'''
            <tr>
                <td>{SEGMENTOS[seg]['nome']}</td>
                <td><strong>{a['nome']}</strong></td>
                <td>{a['alunos']}</td>
                <td>{a['nao_alunos']}</td>
                <td class="text-success">R$ {a['receita_mensal']:,.0f}</td>
                <td class="text-danger">R$ {a['custo_total_mensal']:,.0f}</td>
                <td class="{ 'text-success' if a['lucro_mensal'] >= 0 else 'text-danger' }">R$ {a['lucro_mensal']:,.0f}</td>
            </tr>
            '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header bg-success text-white">
                    <h3 class="mb-0"><i class="fas fa-chart-line"></i> {nome_simulacao} - Resultados</h3>
                </div>
                <div class="card-body">
                    <!-- Resumo -->
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card bg-primary text-white">
                                <div class="card-body text-center">
                                    <h3>R$ {resultados.get('receita_mensal_atividades', 0):,.0f}</h3>
                                    <p>Receita Mensal</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-danger text-white">
                                <div class="card-body text-center">
                                    <h3>R$ {resultados.get('custo_mensal_total', 0):,.0f}</h3>
                                    <p>Custo Total Mensal</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-warning text-white">
                                <div class="card-body text-center">
                                    <h3>R$ {resultados.get('investimento_inicial', 0):,.0f}</h3>
                                    <p>Investimento Inicial</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-success text-white">
                                <div class="card-body text-center">
                                    <h2>R$ {resultados.get('lucro_mensal', 0):,.0f}</h2>
                                    <p><strong>Lucro Mensal</strong></p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Indicadores -->
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h4 class="text-primary">{resultados.get('total_participantes', 0)}</h4>
                                    <p>Participantes</p>
                                    <small>{resultados.get('total_alunos', 0)} alunos + {resultados.get('total_nao_alunos', 0)} não-alunos</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h4>{resultados.get('payback_meses', 0):.1f} meses</h4>
                                    <p>Payback</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h4 class="text-success">{resultados.get('roi_percentual', 0):.1f}%</h4>
                                    <p>ROI ({resultados.get('meses_analise', 24)} meses)</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Atividades -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-list"></i> Atividades ({resultados.get('total_atividades', 0)})</h5>
                                </div>
                                <div class="card-body">
                                    <div class="table-responsive">
                                        <table class="table table-hover">
                                            <thead>
                                                <tr>
                                                    <th>Segmento</th>
                                                    <th>Atividade</th>
                                                    <th>Alunos</th>
                                                    <th>Não-Alunos</th>
                                                    <th>Receita</th>
                                                    <th>Custo</th>
                                                    <th>Lucro</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {tabela_atividades}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Ações -->
                    <div class="row">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-secondary text-white">
                                    <h5 class="mb-0">Ações</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <a href="/simulacao" class="btn btn-primary w-100 mb-2">
                                                <i class="fas fa-plus"></i> Nova Simulação
                                            </a>
                                        </div>
                                        <div class="col-md-3">
                                            <a href="/dashboard" class="btn btn-success w-100 mb-2">
                                                <i class="fas fa-history"></i> Histórico
                                            </a>
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-info w-100 mb-2" onclick="window.print()">
                                                <i class="fas fa-print"></i> Imprimir
                                            </button>
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-warning w-100 mb-2" onclick="solicitarEdicao()">
                                                <i class="fas fa-edit"></i> Editar Esta
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    function solicitarEdicao() {{
        // Armazenar ID para edição
        fetch('/api/marcar_para_edicao', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }}
        }})
        .then(() => {{
            window.location.href = '/dashboard';
        }});
    }}
    </script>
    '''
    return get_base_html(f"Resultados - {nome_simulacao}", content)

@app.route('/api/marcar_para_edicao', methods=['POST'])
def api_marcar_para_edicao():
    """API para marcar simulação para edição"""
    # Usaremos a última simulação da sessão
    if 'ultima_simulacao_flexivel' in session:
        session['simulacao_para_editar'] = session['ultima_simulacao_flexivel']
    return jsonify({'success': True})

@app.route('/dashboard')
def dashboard():
    """Dashboard com histórico e edição"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Últimas simulações
        cursor.execute('''
        SELECT * FROM simulacoes 
        ORDER BY data_criacao DESC 
        LIMIT 20
        ''')
        simulacoes = cursor.fetchall()
        conn.close()
        
        # Verificar se há simulação para editar
        simulacao_para_editar = session.get('simulacao_para_editar')
        if simulacao_para_editar:
            # Limpar após usar
            session.pop('simulacao_para_editar', None)
        
        # Tabela
        tabela_html = ""
        for s in simulacoes:
            data_formatada = datetime.strptime(s['data_criacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            
            # Extrair dados para preview
            dados = json.loads(s['dados_completos'])
            atividades_count = len(dados.get('atividades', []))
            
            tabela_html += f'''
            <tr>
                <td>{data_formatada}</td>
                <td>
                    <strong>{s['nome'][:25]}{'...' if len(s['nome']) > 25 else ''}</strong>
                    <br><small class="text-muted">{atividades_count} atividades</small>
                </td>
                <td>{s['total_participantes']}</td>
                <td>R$ {s['investimento_total']:,.0f}</td>
                <td><span class="badge {'bg-success' if s['roi_percentual'] > 100 else 'bg-warning'}">{s['roi_percentual']:.1f}%</span></td>
                <td>{s['payback_meses']:.1f} meses</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-info" onclick="verSimulacao({s['id']})" title="Ver">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="editarSimulacao({s['id']})" title="Editar">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="excluirSimulacao({s['id']})" title="Excluir">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
            '''
        
        if not simulacoes:
            tabela_html = '''
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="fas fa-inbox fa-2x text-muted mb-2"></i>
                    <p>Nenhuma simulação encontrada</p>
                    <a href="/simulacao" class="btn btn-primary">Nova Simulação</a>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="row">
            <div class="col-12">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0"><i class="fas fa-history"></i> Histórico de Simulações</h3>
                    </div>
                    <div class="card-body">
                        {f'''
                        <div class="alert alert-warning alert-dismissible fade show mb-4" role="alert">
                            <h5><i class="fas fa-edit"></i> Pronto para editar!</h5>
                            <p>Você tem uma simulação carregada para edição.</p>
                            <button type="button" class="btn btn-warning" onclick="continuarEdicao()">
                                <i class="fas fa-edit"></i> Continuar Edição
                            </button>
                            <button type="button" class="btn-close" onclick="cancelarEdicao()"></button>
                        </div>
                        ''' if simulacao_para_editar else ''}
                        
                        <!-- Tabela -->
                        <div class="card">
                            <div class="card-header bg-dark text-white">
                                <h5 class="mb-0">Todas as Simulações</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Data</th>
                                                <th>Nome</th>
                                                <th>Participantes</th>
                                                <th>Investimento</th>
                                                <th>ROI</th>
                                                <th>Payback</th>
                                                <th>Ações</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {tabela_html}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Ações -->
                        <div class="row mt-4">
                            <div class="col-md-4">
                                <a href="/simulacao" class="btn btn-primary w-100">
                                    <i class="fas fa-plus-circle"></i> Nova Simulação
                                </a>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-success w-100" onclick="exportarTudo()">
                                    <i class="fas fa-download"></i> Exportar Tudo
                                </button>
                            </div>
                            <div class="col-md-4">
                                <a href="/" class="btn btn-secondary w-100">
                                    <i class="fas fa-home"></i> Início
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modal para visualização -->
        <div class="modal fade" id="modalVisualizar" tabindex="-1">
            <div class="modal-dialog modal-lg modal-lg-custom">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">Visualizar Simulação</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="modalVisualizarBody">
                        <!-- Conteúdo carregado via JavaScript -->
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function continuarEdicao() {{
            window.location.href = '/simulacao';
        }}
        
        function cancelarEdicao() {{
            fetch('/api/limpar_edicao', {{ method: 'POST' }})
            .then(() => {{
                document.querySelector('.alert').remove();
            }});
        }}
        
        function verSimulacao(id) {{
            fetch(`/api/get_simulacao/${{id}}`)
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    const modalBody = document.getElementById('modalVisualizarBody');
                    modalBody.innerHTML = `
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Informações Gerais</h6>
                                <p><strong>Nome:</strong> ${{data.data.nome}}</p>
                                <p><strong>Data:</strong> ${{data.data.data_criacao}}</p>
                                <p><strong>Participantes:</strong> ${{data.data.total_participantes}}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>Resultados</h6>
                                <p><strong>Investimento:</strong> R$ ${{data.data.investimento_total.toLocaleString('pt-BR')}}</p>
                                <p><strong>Lucro Mensal:</strong> R$ ${{data.data.lucro_mensal_total.toLocaleString('pt-BR')}}</p>
                                <p><strong>ROI:</strong> <span class="badge ${{data.data.roi_percentual > 100 ? 'bg-success' : 'bg-warning'}}">${{data.data.roi_percentual.toFixed(1)}}%</span></p>
                            </div>
                        </div>
                        <div class="mt-3">
                            <a href="/simulacao/${{id}}" class="btn btn-warning">
                                <i class="fas fa-edit"></i> Editar Esta Simulação
                            </a>
                            <button class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    `;
                    
                    const modal = new bootstrap.Modal(document.getElementById('modalVisualizar'));
                    modal.show();
                }} else {{
                    alert('Erro ao carregar simulação');
                }}
            }});
        }}
        
        function editarSimulacao(id) {{
            window.location.href = `/simulacao/${{id}}`;
        }}
        
        function excluirSimulacao(id) {{
            if (confirm('Tem certeza que deseja excluir esta simulação?')) {{
                fetch(`/api/excluir_simulacao/${{id}}`, {{
                    method: 'DELETE'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('Simulação excluída!');
                        window.location.reload();
                    }} else {{
                        alert('Erro: ' + data.error);
                    }}
                }});
            }}
        }}
        
        function exportarTudo() {{
            alert('Exportando todas as simulações...');
            // Implementar exportação CSV/Excel
        }}
        </script>
        '''
        return get_base_html("Histórico", content)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return redirect('/')

@app.route('/api/get_simulacao/<int:simulacao_id>')
def api_get_simulacao(simulacao_id):
    """API para obter dados de uma simulação"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (simulacao_id,))
        simulacao = cursor.fetchone()
        conn.close()
        
        if simulacao:
            return jsonify({
                'success': True,
                'data': dict(simulacao)
            })
        else:
            return jsonify({'success': False, 'error': 'Simulação não encontrada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/excluir_simulacao/<int:simulacao_id>', methods=['DELETE'])
def api_excluir_simulacao(simulacao_id):
    """API para excluir simulação"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM atividades_simulacao WHERE simulacao_id = ?', (simulacao_id,))
        cursor.execute('DELETE FROM simulacoes WHERE id = ?', (simulacao_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/limpar_edicao', methods=['POST'])
def api_limpar_edicao():
    """API para limpar dados de edição"""
    session.pop('simulacao_para_editar', None)
    return jsonify({'success': True})

@app.route('/gerenciar')
def gerenciar():
    """Página de gerenciamento"""
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-cog"></i> Gerenciamento</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-database"></i> Banco de Dados</h5>
                                </div>
                                <div class="card-body">
                                    <p>Gerencie o banco de dados do sistema.</p>
                                    <button class="btn btn-info w-100 mb-2" onclick="exportarBanco()">
                                        <i class="fas fa-download"></i> Exportar Backup
                                    </button>
                                    <button class="btn btn-warning w-100 mb-2" onclick="limparAntigas()">
                                        <i class="fas fa-broom"></i> Limrar Antigas
                                    </button>
                                    <button class="btn btn-danger w-100" onclick="limparTudo()">
                                        <i class="fas fa-trash"></i> Limpar Tudo
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-line"></i> Relatórios</h5>
                                </div>
                                <div class="card-body">
                                    <p>Gere relatórios e análises.</p>
                                    <button class="btn btn-success w-100 mb-2" onclick="gerarRelatorio()">
                                        <i class="fas fa-file-pdf"></i> Relatório PDF
                                    </button>
                                    <button class="btn btn-secondary w-100 mb-2" onclick="gerarExcel()">
                                        <i class="fas fa-file-excel"></i> Exportar Excel
                                    </button>
                                    <button class="btn btn-primary w-100" onclick="analiseComparativa()">
                                        <i class="fas fa-chart-bar"></i> Análise Comparativa
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-warning text-dark">
                                    <h5 class="mb-0"><i class="fas fa-info-circle"></i> Informações do Sistema</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-4">
                                            <h6>Estatísticas</h6>
                                            <p><small>Simulações salvas: <span id="totalSimulacoes">Carregando...</span></small></p>
                                            <p><small>Atividades cadastradas: <span id="totalAtividades">Carregando...</span></small></p>
                                        </div>
                                        <div class="col-md-4">
                                            <h6>Sistema</h6>
                                            <p><small>Versão: 2.0 com Edição</small></p>
                                            <p><small>Banco: SQLite</small></p>
                                        </div>
                                        <div class="col-md-4">
                                            <h6>Ações Rápidas</h6>
                                            <a href="/dashboard" class="btn btn-sm btn-outline-primary w-100 mb-2">
                                                Histórico
                                            </a>
                                            <a href="/simulacao" class="btn btn-sm btn-outline-success w-100">
                                                Nova Simulação
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        carregarEstatisticas();
    }});
    
    function carregarEstatisticas() {{
        fetch('/api/estatisticas')
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                document.getElementById('totalSimulacoes').textContent = data.total_simulacoes;
                document.getElementById('totalAtividades').textContent = data.total_atividades;
            }}
        }});
    }}
    
    function exportarBanco() {{
        alert('Exportando backup do banco de dados...');
        // Implementar exportação
    }}
    
    function limparAntigas() {{
        if (confirm('Limpar simulações com mais de 90 dias?')) {{
            fetch('/api/limpar_antigas', {{ method: 'POST' }})
            .then(response => response.json())
            .then(data => {{
                alert(data.message);
                carregarEstatisticas();
            }});
        }}
    }}
    
    function limparTudo() {{
        if (confirm('TEM CERTEZA? Isso excluirá TODAS as simulações!')) {{
            fetch('/api/limpar_tudo', {{ method: 'POST' }})
            .then(response => response.json())
            .then(data => {{
                alert(data.message);
                carregarEstatisticas();
            }});
        }}
    }}
    
    function gerarRelatorio() {{
        alert('Gerando relatório PDF...');
    }}
    
    function gerarExcel() {{
        alert('Exportando para Excel...');
    }}
    
    function analiseComparativa() {{
        alert('Abrindo análise comparativa...');
    }}
    </script>
    '''
    return get_base_html("Gerenciamento", content)

@app.route('/api/estatisticas')
def api_estatisticas():
    """API para estatísticas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM simulacoes')
        total_simulacoes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM atividades_simulacao')
        total_atividades = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_simulacoes': total_simulacoes,
            'total_atividades': total_atividades
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/limpar_antigas', methods=['POST'])
def api_limpar_antigas():
    """API para limpar simulações antigas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM simulacoes WHERE date(data_criacao) < date('now', '-90 days')")
        excluidas = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{excluidas} simulações antigas foram removidas'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/limpar_tudo', methods=['POST'])
def api_limpar_tudo():
    """API para limpar tudo (cuidado!)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM atividades_simulacao')
        cursor.execute('DELETE FROM simulacoes')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Todas as simulações foram removidas'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Inicializar banco
    init_db()
    
    print("=" * 70)
    print("🚀 BUSINESS PLAN ESCOLAR - VERSÃO COMPLETA COM EDIÇÃO")
    print("=" * 70)
    print("✅ Atividades livres - digite qualquer nome")
    print("✅ Edição completa de todos os valores")
    print("✅ Cálculos baseados em recursos reais")
    print("✅ Histórico com opção de editar/excluir")
    print("✅ Dashboard completo com gerenciamento")
    print("=" * 70)
    print("🎯 Funcionalidades principais:")
    print("   1. Adicione atividades em qualquer segmento")
    print("   2. Configure custos por hora, horas semanais")
    print("   3. Edite simulações salvas")
    print("   4. Exclua simulações antigas")
    print("   5. Visualize gráficos em tempo real")
    print("=" * 70)
    print("🌐 Acesse: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000/dashboard")
    print("⚙️ Gerenciar: http://localhost:5000/gerenciar")
    print("=" * 70)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
