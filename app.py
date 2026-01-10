# app_avancado_com_edicao.py
from flask import Flask, render_template_string, request, jsonify, session, redirect, flash
from datetime import datetime
import json
import math
import os
import sqlite3
import traceback

app = Flask(__name__)

# Configuração
app.config['SECRET_KEY'] = 'business_plan_escolar_avancado_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'database_avancado.db')

# Dados padrão por segmento
SEGMENTOS = {
    'ei': {
        'nome': 'Educação Infantil',
        'cor': '#FF6B8B',
        'atividades': ['Música', 'Artes', 'Psicomotricidade', 'Contação de Histórias'],
        'ratio_aluno_professor': 10,
        'custo_professor_hora': 45
    },
    'ef_i': {
        'nome': 'Ensino Fundamental I',
        'cor': '#4ECDC4',
        'atividades': ['Robótica', 'Programação', 'Teatro', 'Esportes', 'Inglês'],
        'ratio_aluno_professor': 15,
        'custo_professor_hora': 50
    },
    'ef_ii': {
        'nome': 'Ensino Fundamental II',
        'cor': '#45B7D1',
        'atividades': ['Robótica Avançada', 'Olimpíadas Científicas', 'Debate', 'Música Instrumental'],
        'ratio_aluno_professor': 20,
        'custo_professor_hora': 55
    },
    'em': {
        'nome': 'Ensino Médio',
        'cor': '#FF9F1C',
        'atividades': ['Preparatório ENEM', 'Orientação Profissional', 'Projetos Científicos', 'Empreendedorismo'],
        'ratio_aluno_professor': 25,
        'custo_professor_hora': 65
    }
}

# Categorias de custos
CATEGORIAS_CUSTOS = {
    'infraestrutura': [
        'Reforma de salas',
        'Equipamentos tecnológicos',
        'Materiais esportivos',
        'Instrumentos musicais',
        'Mobiliário especializado',
        'Kit robótica/programação'
    ],
    'material': [
        'Material didático',
        'Kits de atividades',
        'Uniformes',
        'Material de consumo',
        'Livros paradidáticos'
    ],
    'marketing': [
        'Site e redes sociais',
        'Material impresso',
        'Eventos de divulgação',
        'Publicidade online',
        'Produção de vídeos'
    ],
    'recursos_humanos': [
        'Capacitação de professores',
        'Contratação especialistas',
        'Equipe de apoio',
        'Benefícios e encargos'
    ],
    'custos_mensais': [
        'Salário professores',
        'Manutenção e limpeza',
        'Utilities (luz, água, gás)',
        'Seguro e vigilância',
        'Telefone e internet',
        'Materiais de consumo mensal'
    ]
}

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Tabela de simulações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            data_atualizacao TEXT,
            usuario TEXT DEFAULT 'admin',
            total_alunos INTEGER,
            investimento_total REAL,
            custo_mensal_total REAL,
            receita_mensal_total REAL,
            lucro_mensal_total REAL,
            payback_total REAL,
            roi_total REAL,
            dados TEXT,
            segmentos_detalhados TEXT
        )
        ''')
        
        # Tabela de segmentos por simulação
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS segmentos_simulacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulacao_id INTEGER,
            segmento TEXT,
            alunos INTEGER,
            participantes_alunos INTEGER,
            participantes_nao_alunos INTEGER,
            receita_alunos REAL,
            receita_nao_alunos REAL,
            custo_segmento REAL,
            receita_segmento REAL,
            lucro_segmento REAL,
            FOREIGN KEY (simulacao_id) REFERENCES simulacoes (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados avançado inicializado!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

def get_base_html(title="Business Plan Escolar", content=""):
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
    <style>
        :root {{
            --ei-color: #FF6B8B;
            --ef-i-color: #4ECDC4;
            --ef-ii-color: #45B7D1;
            --em-color: #FF9F1C;
        }}
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .navbar-brand {{ font-weight: 700; }}
        .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .card-header {{ border-radius: 10px 10px 0 0 !important; }}
        .btn-primary {{ background-color: #4361ee; border-color: #4361ee; }}
        .btn-primary:hover {{ background-color: #3a0ca3; border-color: #3a0ca3; }}
        .segmento-ei {{ border-left: 5px solid var(--ei-color) !important; }}
        .segmento-ef-i {{ border-left: 5px solid var(--ef-i-color) !important; }}
        .segmento-ef-ii {{ border-left: 5px solid var(--ef-ii-color) !important; }}
        .segmento-em {{ border-left: 5px solid var(--em-color) !important; }}
        .badge-ei {{ background-color: var(--ei-color) !important; }}
        .badge-ef-i {{ background-color: var(--ef-i-color) !important; }}
        .badge-ef-ii {{ background-color: var(--ef-ii-color) !important; }}
        .badge-em {{ background-color: var(--em-color) !important; }}
        .sticky-summary {{ position: sticky; top: 20px; }}
        footer {{ background-color: #2c3e50; color: white; padding: 20px 0; margin-top: 40px; }}
        .segmento-card {{ transition: transform 0.3s; }}
        .segmento-card:hover {{ transform: translateY(-5px); }}
        .chart-container {{ position: relative; height: 300px; width: 100%; }}
        .action-buttons {{ position: absolute; top: 10px; right: 10px; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line"></i> Business Plan Avançado
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Início</a>
                <a class="nav-link" href="/simulacao"><i class="fas fa-calculator"></i> Nova Simulação</a>
                <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {content}
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container text-center">
            <p>Sistema Avançado de Business Plan Escolar com Edição</p>
            <p class="mb-0">© 2024 - Edite e recalcule suas simulações</p>
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
                        <i class="fas fa-school"></i> Business Plan com Edição
                    </h1>
                    <p class="lead mb-4">
                        Crie, edite e recalcule simulações por segmento escolar
                    </p>
                    <div class="row mt-4">
                        <div class="col-md-4">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-edit fa-3x text-primary mb-3"></i>
                                    <h5>Edição Completa</h5>
                                    <p>Modifique simulações salvas</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-layer-group fa-3x text-success mb-3"></i>
                                    <h5>4 Segmentos</h5>
                                    <p>EI, EF I, EF II, EM</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-light text-dark">
                                <div class="card-body">
                                    <i class="fas fa-redo fa-3x text-warning mb-3"></i>
                                    <h5>Recálculo</h5>
                                    <p>Atualize resultados automaticamente</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <a href="/simulacao" class="btn btn-light btn-lg mt-4">
                        <i class="fas fa-play-circle"></i> Nova Simulação
                    </a>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan com Edição", content)

@app.route('/simulacao')
@app.route('/simulacao/<int:simulacao_id>')
def simulacao(simulacao_id=None):
    """Página de simulação com ou sem edição"""
    
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
                dados_completos = json.loads(simulacao['dados'])
                dados_edicao = {
                    'nome': simulacao['nome'],
                    'dados_entrada': dados_completos.get('entrada', {}),
                    'resultados': dados_completos.get('resultados', {}),
                    'segmentos_detalhados': json.loads(simulacao['segmentos_detalhados'] or '{}'),
                    'custos_detalhados': dados_completos.get('custos_detalhados', {})
                }
            
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar simulação para edição: {e}")
            return redirect('/dashboard')
    
    # Gerar HTML para os segmentos (com dados de edição se existirem)
    segmentos_html = ""
    for sigla, info in SEGMENTOS.items():
        # Valores padrão ou de edição
        alunos_valor = dados_edicao.get('dados_entrada', {}).get('segmentos', {}).get(sigla, {}).get('alunos', 50)
        part_alunos_valor = dados_edicao.get('dados_entrada', {}).get('segmentos', {}).get(sigla, {}).get('participantes_alunos', 20)
        part_nao_alunos_valor = dados_edicao.get('dados_entrada', {}).get('segmentos', {}).get(sigla, {}).get('participantes_nao_alunos', 5)
        receita_alunos_valor = dados_edicao.get('dados_entrada', {}).get('segmentos', {}).get(sigla, {}).get('receita_alunos', info['custo_professor_hora'] + 30)
        receita_nao_alunos_valor = dados_edicao.get('dados_entrada', {}).get('segmentos', {}).get(sigla, {}).get('receita_nao_alunos', info['custo_professor_hora'] + 50)
        
        segmentos_html += f'''
        <div class="col-md-6 mb-4">
            <div class="card segmento-card segmento-{sigla.replace('_', '-')}">
                <div class="card-header" style="background-color: {info['cor']}; color: white;">
                    <h5 class="mb-0"><i class="fas fa-graduation-cap"></i> {info['nome']}</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Total de alunos ({info['nome']}):</label>
                        <input type="number" class="form-control segmento-alunos" 
                               data-segmento="{sigla}"
                               id="alunos_{sigla}"
                               value="{alunos_valor}"
                               min="0">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Alunos participantes:</label>
                        <input type="number" class="form-control segmento-participantes" 
                               data-segmento="{sigla}"
                               data-tipo="alunos"
                               id="participantes_alunos_{sigla}"
                               value="{part_alunos_valor}"
                               min="0">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Não-alunos participantes:</label>
                        <input type="number" class="form-control segmento-participantes" 
                               data-segmento="{sigla}"
                               data-tipo="nao_alunos"
                               id="participantes_nao_alunos_{sigla}"
                               value="{part_nao_alunos_valor}"
                               min="0">
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <div class="mb-3">
                                <label class="form-label">Receita aluno (R$/mês):</label>
                                <input type="number" class="form-control segmento-receita" 
                                       data-segmento="{sigla}"
                                       data-tipo="alunos"
                                       id="receita_alunos_{sigla}"
                                       value="{receita_alunos_valor}"
                                       min="0">
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="mb-3">
                                <label class="form-label">Receita não-aluno (R$/mês):</label>
                                <input type="number" class="form-control segmento-receita" 
                                       data-segmento="{sigla}"
                                       data-tipo="nao_alunos"
                                       id="receita_nao_alunos_{sigla}"
                                       value="{receita_nao_alunos_valor}"
                                       min="0">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    # Gerar campos de custo (com dados de edição se existirem)
    campos_custos = ""
    categorias = ['infraestrutura', 'material', 'marketing', 'recursos_humanos', 'custos_mensais']
    cores = ['info', 'success', 'warning', 'primary', 'secondary']
    
    for i, (categoria, cor) in enumerate(zip(categorias, cores)):
        campos_custos += f'''
        <div class="col-md-6 mb-4">
            <div class="card">
                <div class="card-header bg-{cor} text-white">
                    <h5 class="mb-0"><i class="fas fa-{['tools', 'book', 'bullhorn', 'users', 'dollar-sign'][i]}"></i> {categoria.title()}</h5>
                </div>
                <div class="card-body">
        '''
        
        for item in CATEGORIAS_CUSTOS[categoria]:
            campo_id = f"{categoria}_{item.replace(' ', '_').lower()}"
            is_mensal = categoria == 'custos_mensais'
            
            # Buscar valor de edição se existir
            valor_edicao = 0
            if dados_edicao.get('custos_detalhados', {}).get(categoria, {}).get(item, {}):
                valor_edicao = dados_edicao['custos_detalhados'][categoria][item].get('valor', 0)
            
            campos_custos += f'''
            <div class="mb-3">
                <label class="form-label">{item}{' (mensal)' if is_mensal else ''}:</label>
                <div class="input-group">
                    <span class="input-group-text">R$</span>
                    <input type="number" class="form-control campo-custo" 
                           id="{campo_id}"
                           data-categoria="{categoria}"
                           data-item="{item}"
                           {"data-mensal='true'" if is_mensal else ""}
                           value="{valor_edicao}"
                           min="0" 
                           step="100">
                </div>
            </div>
            '''
        
        campos_custos += '''
                </div>
            </div>
        </div>
        '''
    
    # Botão de ação específico (salvar novo ou atualizar)
    botao_acao = "Calcular Simulação"
    acao_js = "calcularSimulacao()"
    if modo_edicao:
        botao_acao = "Atualizar Simulação"
        acao_js = f"atualizarSimulacao({simulacao_id})"
    
    titulo_pagina = "Editar Simulação" if modo_edicao else "Nova Simulação"
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> {titulo_pagina}</h3>
                    {"<p class='mb-0'><small>Editando simulação #" + str(simulacao_id) + "</small></p>" if modo_edicao else ""}
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
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Nome da Simulação:</label>
                                    <input type="text" class="form-control" id="nome_simulacao" 
                                           value="{dados_edicao.get('nome', 'Simulação ' + datetime.now().strftime('%d/%m/%Y'))}">
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Aumento esperado (%):</label>
                                    <input type="number" class="form-control" id="aumento_esperado" 
                                           value="{dados_edicao.get('dados_entrada', {}).get('aumento_esperado', 15)}" 
                                           min="0" max="100">
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Horas semanais/atividade:</label>
                                    <input type="number" class="form-control" id="horas_semanais" 
                                           value="{dados_edicao.get('dados_entrada', {}).get('horas_semanais', 10)}" 
                                           min="1">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Segmentos -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-layer-group"></i> Configuração por Segmento
                                </h4>
                                <p class="text-muted">Configure cada segmento separadamente.</p>
                            </div>
                            
                            {segmentos_html}
                        </div>
                        
                        <!-- Custos -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-money-bill-wave"></i> Custos
                                </h4>
                                <p class="text-muted">Preencha os custos relevantes para o projeto.</p>
                                <div class="row">
                                    {campos_custos}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo e Ações -->
                        <div class="row">
                            <div class="col-md-6">
                                <div class="sticky-summary">
                                    <div class="card">
                                        <div class="card-header bg-success text-white">
                                            <h5 class="mb-0"><i class="fas fa-chart-line"></i> Resumo</h5>
                                        </div>
                                        <div class="card-body">
                                            <div id="resumo_simulacao">
                                                <p>Preencha os dados para ver o resumo</p>
                                            </div>
                                            
                                            <div class="mt-3">
                                                <button type="button" class="btn btn-primary w-100 mb-2" onclick="{acao_js}">
                                                    <i class="fas fa-save"></i> {botao_acao}
                                                </button>
                                                <button type="button" class="btn btn-outline-secondary w-100" onclick="resetForm()">
                                                    <i class="fas fa-redo"></i> Limpar Tudo
                                                </button>
                                                {f'<a href="/dashboard" class="btn btn-outline-warning w-100 mt-2"><i class="fas fa-times"></i> Cancelar Edição</a>' if modo_edicao else ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div id="resultado_preview" style="display: none;">
                                    <!-- Preview aparecerá aqui -->
                                </div>
                                <div id="graficos_container" class="mt-3">
                                    <!-- Gráficos aparecerão aqui -->
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Configurar eventos para todos os campos
        const campos = ['nome_simulacao', 'aumento_esperado', 'horas_semanais'];
        campos.forEach(id => {{
            document.getElementById(id).addEventListener('input', atualizarResumo);
        }});
        
        // Eventos para segmentos
        document.querySelectorAll('.segmento-alunos, .segmento-participantes, .segmento-receita').forEach(campo => {{
            campo.addEventListener('input', atualizarResumo);
        }});
        
        // Eventos para custos
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            campo.addEventListener('input', atualizarResumo);
        }});
        
        // Inicializar
        atualizarResumo();
    }});
    
    function atualizarResumo() {{
        // Coletar dados dos segmentos
        let totalAlunos = 0;
        let totalParticipantesAlunos = 0;
        let totalParticipantesNaoAlunos = 0;
        let receitaMensalTotal = 0;
        let segmentosAtivos = 0;
        
        const segmentos = ['ei', 'ef_i', 'ef_ii', 'em'];
        const dadosSegmentos = {{}};
        
        segmentos.forEach(seg => {{
            const alunos = parseInt(document.getElementById(`alunos_${{seg}}`).value) || 0;
            const partAlunos = parseInt(document.getElementById(`participantes_alunos_${{seg}}`).value) || 0;
            const partNaoAlunos = parseInt(document.getElementById(`participantes_nao_alunos_${{seg}}`).value) || 0;
            const receitaAlunos = parseFloat(document.getElementById(`receita_alunos_${{seg}}`).value) || 0;
            const receitaNaoAlunos = parseFloat(document.getElementById(`receita_nao_alunos_${{seg}}`).value) || 0;
            
            if (alunos > 0 || partAlunos > 0 || partNaoAlunos > 0) {{
                segmentosAtivos++;
                totalAlunos += alunos;
                totalParticipantesAlunos += partAlunos;
                totalParticipantesNaoAlunos += partNaoAlunos;
                
                const receitaSegmento = (partAlunos * receitaAlunos) + (partNaoAlunos * receitaNaoAlunos);
                receitaMensalTotal += receitaSegmento;
                
                dadosSegmentos[seg] = {{
                    alunos: alunos,
                    participantesAlunos: partAlunos,
                    participantesNaoAlunos: partNaoAlunos,
                    receita: receitaSegmento,
                    cor: {{
                        'ei': '#FF6B8B',
                        'ef_i': '#4ECDC4',
                        'ef_ii': '#45B7D1',
                        'em': '#FF9F1C'
                    }}[seg]
                }};
            }}
        }});
        
        // Calcular custos
        let investimentoTotal = 0;
        let custoMensalTotal = 0;
        
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            const valor = parseFloat(campo.value) || 0;
            const isMensal = campo.hasAttribute('data-mensal');
            
            if (isMensal) {{
                custoMensalTotal += valor;
            }} else {{
                investimentoTotal += valor;
            }}
        }});
        
        // Calcular indicadores
        const lucroMensal = receitaMensalTotal - custoMensalTotal;
        let paybackMeses = 0;
        let roiPercentual = 0;
        
        if (lucroMensal > 0 && investimentoTotal > 0) {{
            paybackMeses = investimentoTotal / lucroMensal;
            roiPercentual = (lucroMensal * 12 / investimentoTotal) * 100;
        }}
        
        // Atualizar resumo
        const resumoHTML = `
            <table class="table table-sm">
                <tr>
                    <td>Segmentos ativos:</td>
                    <td class="text-end"><span class="badge bg-primary">${{segmentosAtivos}}/4</span></td>
                </tr>
                <tr>
                    <td>Total de alunos:</td>
                    <td class="text-end"><strong>${{totalAlunos}}</strong></td>
                </tr>
                <tr>
                    <td>Participantes totais:</td>
                    <td class="text-end text-success">
                        <strong>${{totalParticipantesAlunos + totalParticipantesNaoAlunos}}</strong>
                    </td>
                </tr>
                <tr>
                    <td>Receita Mensal:</td>
                    <td class="text-end text-success"><strong>R$ ${{receitaMensalTotal.toLocaleString('pt-BR')}}</strong></td>
                </tr>
                <tr>
                    <td>Investimento Total:</td>
                    <td class="text-end">R$ ${{investimentoTotal.toLocaleString('pt-BR')}}</td>
                </tr>
                <tr>
                    <td>Custos Mensais:</td>
                    <td class="text-end">R$ ${{custoMensalTotal.toLocaleString('pt-BR')}}</td>
                </tr>
                <tr class="table-info">
                    <td><strong>Lucro Mensal:</strong></td>
                    <td class="text-end"><strong>R$ ${{lucroMensal.toLocaleString('pt-BR')}}</strong></td>
                </tr>
                <tr>
                    <td>Payback:</td>
                    <td class="text-end">${{paybackMeses.toFixed(1)}} meses</td>
                </tr>
                <tr>
                    <td>ROI Anual:</td>
                    <td class="text-end"><span class="badge ${{roiPercentual > 100 ? 'bg-success' : 'bg-warning'}}">${{roiPercentual.toFixed(1)}}%</span></td>
                </tr>
            </table>
        `;
        
        document.getElementById('resumo_simulacao').innerHTML = resumoHTML;
        
        // Atualizar gráficos
        atualizarGraficos(dadosSegmentos);
    }}
    
    function atualizarGraficos(dadosSegmentos) {{
        const container = document.getElementById('graficos_container');
        
        if (Object.keys(dadosSegmentos).length === 0) {{
            container.innerHTML = '<div class="alert alert-info">Preencha os segmentos para ver os gráficos</div>';
            return;
        }}
        
        // Preparar dados
        const labels = [];
        const participantesData = [];
        const receitaData = [];
        const cores = [];
        
        Object.entries(dadosSegmentos).forEach(([seg, dados]) => {{
            const segNome = {{
                'ei': 'EI',
                'ef_i': 'EF I', 
                'ef_ii': 'EF II',
                'em': 'EM'
            }}[seg];
            
            labels.push(segNome);
            participantesData.push(dados.participantesAlunos + dados.participantesNaoAlunos);
            receitaData.push(dados.receita);
            cores.push(dados.cor);
        }});
        
        const graficosHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-chart-bar"></i> Visualização em Tempo Real</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="chart-container">
                                <canvas id="chartParticipantes"></canvas>
                            </div>
                            <p class="text-center small">Participantes por Segmento</p>
                        </div>
                        <div class="col-md-6">
                            <div class="chart-container">
                                <canvas id="chartReceita"></canvas>
                            </div>
                            <p class="text-center small">Receita por Segmento</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = graficosHTML;
        
        // Criar gráficos após um pequeno delay
        setTimeout(() => {{
            // Gráfico de participantes
            const ctx1 = document.getElementById('chartParticipantes').getContext('2d');
            if (window.chartParticipantes) window.chartParticipantes.destroy();
            window.chartParticipantes = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Participantes',
                        data: participantesData,
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
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
            
            // Gráfico de receita
            const ctx2 = document.getElementById('chartReceita').getContext('2d');
            if (window.chartReceita) window.chartReceita.destroy();
            window.chartReceita = new Chart(ctx2, {{
                type: 'pie',
                data: {{
                    labels: labels,
                    datasets: [{{
                        data: receitaData,
                        backgroundColor: cores,
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ 
                            position: 'bottom',
                            labels: {{
                                padding: 20
                            }}
                        }}
                    }}
                }}
            }});
        }}, 100);
    }}
    
    function resetForm() {{
        if (confirm('Limpar todos os dados?')) {{
            document.getElementById('simulacaoForm').reset();
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                campo.value = 0;
            }});
            // Resetar segmentos para valores padrão
            document.querySelectorAll('.segmento-alunos').forEach(campo => {{
                campo.value = 50;
            }});
            document.querySelectorAll('.segmento-participantes[data-tipo="alunos"]').forEach(campo => {{
                campo.value = 20;
            }});
            document.querySelectorAll('.segmento-participantes[data-tipo="nao_alunos"]').forEach(campo => {{
                campo.value = 5;
            }});
            atualizarResumo();
        }}
    }}
    
    async function calcularSimulacao() {{
        await enviarSimulacao('/api/calcular_avancado', 'POST');
    }}
    
    async function atualizarSimulacao(simulacaoId) {{
        await enviarSimulacao(`/api/atualizar_simulacao/${{simulacaoId}}`, 'PUT');
    }}
    
    async function enviarSimulacao(url, metodo) {{
        const btn = document.querySelector('button[onclick*="Simulacao"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
        btn.disabled = true;
        
        try {{
            // Coletar dados gerais
            const dados = {{
                nome: document.getElementById('nome_simulacao').value,
                aumento_esperado: parseInt(document.getElementById('aumento_esperado').value) || 0,
                horas_semanais: parseInt(document.getElementById('horas_semanais').value) || 0
            }};
            
            // Coletar dados dos segmentos
            dados.segmentos = {{}};
            const segmentos = ['ei', 'ef_i', 'ef_ii', 'em'];
            
            segmentos.forEach(seg => {{
                dados.segmentos[seg] = {{
                    alunos: parseInt(document.getElementById(`alunos_${{seg}}`).value) || 0,
                    participantes_alunos: parseInt(document.getElementById(`participantes_alunos_${{seg}}`).value) || 0,
                    participantes_nao_alunos: parseInt(document.getElementById(`participantes_nao_alunos_${{seg}}`).value) || 0,
                    receita_alunos: parseFloat(document.getElementById(`receita_alunos_${{seg}}`).value) || 0,
                    receita_nao_alunos: parseFloat(document.getElementById(`receita_nao_alunos_${{seg}}`).value) || 0
                }};
            }});
            
            // Coletar custos
            dados.custos_detalhados = {{}};
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                const categoria = campo.getAttribute('data-categoria');
                const item = campo.getAttribute('data-item');
                const valor = parseFloat(campo.value) || 0;
                const isMensal = campo.hasAttribute('data-mensal');
                
                if (!dados.custos_detalhados[categoria]) {{
                    dados.custos_detalhados[categoria] = {{}};
                }}
                dados.custos_detalhados[categoria][item] = {{
                    valor: valor,
                    mensal: isMensal
                }};
            }});
            
            // Enviar para API
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
            
            // Mostrar mensagem de sucesso
            document.getElementById('resultado_preview').innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> Simulação salva com sucesso!</h5>
                    <p>Redirecionando para análise completa...</p>
                </div>
            `;
            document.getElementById('resultado_preview').style.display = 'block';
            
            // Redirecionar após 2 segundos
            setTimeout(() => {{
                window.location.href = '/resultado_avancado';
            }}, 2000);
            
        }} catch (error) {{
            console.error('Erro:', error);
            alert('Erro ao processar simulação: ' + error.message);
        }} finally {{
            btn.innerHTML = originalText;
            btn.disabled = false;
        }}
    }}
    </script>
    '''
    return get_base_html(titulo_pagina, content)

@app.route('/api/calcular_avancado', methods=['POST'])
def api_calcular_avancado():
    """API para cálculo de nova simulação"""
    return processar_simulacao(request)

@app.route('/api/atualizar_simulacao/<int:simulacao_id>', methods=['PUT'])
def api_atualizar_simulacao(simulacao_id):
    """API para atualizar simulação existente"""
    return processar_simulacao(request, simulacao_id)

def processar_simulacao(request_obj, simulacao_id=None):
    """Processa simulação (nova ou atualização)"""
    try:
        dados = request_obj.get_json()
        if not dados:
            return jsonify({'error': 'Nenhum dado recebido'}), 400
        
        print(f"Processando simulação {'#{}'.format(simulacao_id) if simulacao_id else 'nova'}")
        
        # Inicializar totais
        totais = {
            'alunos_escola': 0,
            'participantes_alunos': 0,
            'participantes_nao_alunos': 0,
            'receita_mensal': 0,
            'investimento_total': 0,
            'custo_mensal': 0,
            'lucro_mensal': 0
        }
        
        # Processar segmentos
        segmentos_detalhados = {}
        segmentos = dados.get('segmentos', {})
        
        for sigla, info in segmentos.items():
            alunos = int(info.get('alunos', 0) or 0)
            part_alunos = int(info.get('participantes_alunos', 0) or 0)
            part_nao_alunos = int(info.get('participantes_nao_alunos', 0) or 0)
            receita_alunos = float(info.get('receita_alunos', 0) or 0)
            receita_nao_alunos = float(info.get('receita_nao_alunos', 0) or 0)
            
            if alunos > 0 or part_alunos > 0 or part_nao_alunos > 0:
                # Calcular para este segmento
                receita_segmento = (part_alunos * receita_alunos) + (part_nao_alunos * receita_nao_alunos)
                
                # Atualizar totais
                totais['alunos_escola'] += alunos
                totais['participantes_alunos'] += part_alunos
                totais['participantes_nao_alunos'] += part_nao_alunos
                totais['receita_mensal'] += receita_segmento
                
                # Salvar detalhes do segmento
                segmentos_detalhados[sigla] = {
                    'nome': SEGMENTOS[sigla]['nome'],
                    'alunos': alunos,
                    'participantes_alunos': part_alunos,
                    'participantes_nao_alunos': part_nao_alunos,
                    'receita_alunos': receita_alunos,
                    'receita_nao_alunos': receita_nao_alunos,
                    'receita_segmento': receita_segmento,
                    'cor': SEGMENTOS[sigla]['cor']
                }
        
        # Calcular custos
        custos_detalhados = dados.get('custos_detalhados', {})
        for categoria, itens in custos_detalhados.items():
            for item, info in itens.items():
                valor = float(info.get('valor', 0) or 0)
                if info.get('mensal'):
                    totais['custo_mensal'] += valor
                else:
                    totais['investimento_total'] += valor
        
        # Calcular lucro
        totais['lucro_mensal'] = totais['receita_mensal'] - totais['custo_mensal']
        
        # Calcular indicadores
        payback_meses = 0
        roi_percentual = 0
        
        if totais['lucro_mensal'] > 0 and totais['investimento_total'] > 0:
            payback_meses = totais['investimento_total'] / totais['lucro_mensal']
            roi_percentual = (totais['lucro_mensal'] * 12 / totais['investimento_total']) * 100
        
        # Resultados finais
        resultados = {
            **totais,
            'payback_meses': payback_meses,
            'roi_percentual': roi_percentual,
            'total_participantes': totais['participantes_alunos'] + totais['participantes_nao_alunos'],
            'segmentos_ativos': len(segmentos_detalhados),
            'aumento_esperado': dados.get('aumento_esperado', 0),
            'horas_semanais': dados.get('horas_semanais', 0)
        }
        
        print(f"Resultados calculados para {len(segmentos_detalhados)} segmentos")
        
        # Salvar na sessão
        session['ultima_simulacao_avancada'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'segmentos_detalhados': segmentos_detalhados,
            'custos_detalhados': custos_detalhados,
            'nome_simulacao': dados.get('nome', 'Simulação')
        }
        
        # Salvar/Atualizar no banco
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            if simulacao_id:
                # Atualizar simulação existente
                cursor.execute('''
                UPDATE simulacoes SET
                    nome = ?,
                    data_atualizacao = ?,
                    total_alunos = ?,
                    investimento_total = ?,
                    custo_mensal_total = ?,
                    receita_mensal_total = ?,
                    lucro_mensal_total = ?,
                    payback_total = ?,
                    roi_total = ?,
                    dados = ?,
                    segmentos_detalhados = ?
                WHERE id = ?
                ''', (
                    dados.get('nome', f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    totais['alunos_escola'],
                    totais['investimento_total'],
                    totais['custo_mensal'],
                    totais['receita_mensal'],
                    totais['lucro_mensal'],
                    payback_meses,
                    roi_percentual,
                    json.dumps({
                        'entrada': dados,
                        'resultados': resultados,
                        'custos_detalhados': custos_detalhados
                    }),
                    json.dumps(segmentos_detalhados),
                    simulacao_id
                ))
                
                # Remover segmentos antigos
                cursor.execute('DELETE FROM segmentos_simulacao WHERE simulacao_id = ?', (simulacao_id,))
                
                print(f"✅ Simulação #{simulacao_id} atualizada!")
            else:
                # Inserir nova simulação
                cursor.execute('''
                INSERT INTO simulacoes (
                    nome, data_criacao, data_atualizacao, total_alunos, investimento_total,
                    custo_mensal_total, receita_mensal_total, lucro_mensal_total,
                    payback_total, roi_total, dados, segmentos_detalhados
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dados.get('nome', f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    totais['alunos_escola'],
                    totais['investimento_total'],
                    totais['custo_mensal'],
                    totais['receita_mensal'],
                    totais['lucro_mensal'],
                    payback_meses,
                    roi_percentual,
                    json.dumps({
                        'entrada': dados,
                        'resultados': resultados,
                        'custos_detalhados': custos_detalhados
                    }),
                    json.dumps(segmentos_detalhados)
                ))
                
                simulacao_id = cursor.lastrowid
                print(f"✅ Nova simulação #{simulacao_id} criada!")
            
            # Salvar detalhes dos segmentos
            for sigla, detalhes in segmentos_detalhados.items():
                cursor.execute('''
                INSERT INTO segmentos_simulacao (
                    simulacao_id, segmento, alunos, participantes_alunos,
                    participantes_nao_alunos, receita_alunos, receita_nao_alunos,
                    custo_segmento, receita_segmento, lucro_segmento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    simulacao_id,
                    sigla,
                    detalhes['alunos'],
                    detalhes['participantes_alunos'],
                    detalhes['participantes_nao_alunos'],
                    detalhes['receita_alunos'],
                    detalhes['receita_nao_alunos'],
                    0,
                    detalhes['receita_segmento'],
                    detalhes['receita_segmento']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar no banco: {e}")
        
        return jsonify(resultados)
        
    except Exception as e:
        print(f"❌ ERRO NO PROCESSAMENTO: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Erro interno no processamento'
        }), 500

@app.route('/resultado_avancado')
def resultado_avancado():
    """Página de resultados avançada"""
    if 'ultima_simulacao_avancada' not in session:
        return redirect('/simulacao')
    
    dados = session['ultima_simulacao_avancada']
    resultados = dados['resultados']
    segmentos = dados['segmentos_detalhados']
    nome_simulacao = dados.get('nome_simulacao', 'Simulação')
    
    # HTML dos segmentos
    segmentos_html = ""
    total_segmentos = 0
    if segmentos:
        for sigla, info in segmentos.items():
            total_segmentos += 1
            segmentos_html += f'''
            <div class="col-md-3">
                <div class="card segmento-{sigla.replace('_', '-')}">
                    <div class="card-header" style="background-color: {info['cor']}; color: white;">
                        <h6 class="mb-0">{info['nome']}</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-1"><small>Alunos: {info['alunos']}</small></p>
                        <p class="mb-1"><small>Participantes: {info['participantes_alunos'] + info['participantes_nao_alunos']}</small></p>
                        <p class="mb-0"><small>Receita: R$ {info['receita_segmento']:,.0f}</small></p>
                    </div>
                </div>
            </div>
            '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header bg-success text-white">
                    <h3 class="mb-0"><i class="fas fa-chart-line"></i> {nome_simulacao} - Resultados</h3>
                </div>
                <div class="card-body">
                    <!-- Resumo Principal -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="mb-0">Resumo Financeiro</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <div class="text-center p-3 border rounded">
                                                <h3 class="text-success">R$ {resultados.get('receita_mensal', 0):,.0f}</h3>
                                                <small>Receita Mensal</small>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="text-center p-3 border rounded">
                                                <h3 class="text-warning">R$ {resultados.get('investimento_total', 0):,.0f}</h3>
                                                <small>Investimento</small>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="text-center p-3 border rounded">
                                                <h3 class="text-danger">R$ {resultados.get('custo_mensal', 0):,.0f}</h3>
                                                <small>Custos Mensais</small>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="text-center p-3 border rounded bg-light">
                                                <h2 class="text-success">R$ {resultados.get('lucro_mensal', 0):,.0f}</h2>
                                                <strong>Lucro Mensal</strong>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mt-3">
                                        <div class="col-md-6">
                                            <div class="text-center p-3 border rounded">
                                                <h4>{resultados.get('payback_meses', 0):.1f}</h4>
                                                <small>Payback (meses)</small>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="text-center p-3 border rounded">
                                                <h4 class="text-success">{resultados.get('roi_percentual', 0):.1f}%</h4>
                                                <small>ROI Anual</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card h-100">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0">Participantes</h5>
                                </div>
                                <div class="card-body text-center">
                                    <h1 class="display-3 text-primary">{resultados.get('total_participantes', 0)}</h1>
                                    <p class="lead">Total de Participantes</p>
                                    <div class="row">
                                        <div class="col-6">
                                            <div class="alert alert-info">
                                                <h4>{resultados.get('participantes_alunos', 0)}</h4>
                                                <small>Alunos</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="alert alert-secondary">
                                                <h4>{resultados.get('participantes_nao_alunos', 0)}</h4>
                                                <small>Não-Alunos</small>
                                            </div>
                                        </div>
                                    </div>
                                    <p><small>{total_segmentos} segmentos ativos</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Segmentos -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-warning text-dark">
                                    <h5 class="mb-0"><i class="fas fa-layer-group"></i> Análise por Segmento</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        {segmentos_html if segmentos_html else '<div class="col-12 text-center"><p>Nenhum segmento configurado</p></div>'}
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
                                                <i class="fas fa-tachometer-alt"></i> Dashboard
                                            </a>
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-info w-100 mb-2" onclick="window.print()">
                                                <i class="fas fa-print"></i> Imprimir/PDF
                                            </button>
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-warning w-100 mb-2" onclick="solicitarEdicao()">
                                                <i class="fas fa-edit"></i> Editar Esta Simulação
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
        // Armazenar dados para edição
        fetch('/api/preparar_edicao', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{
                nome_simulacao: "{nome_simulacao}",
                resultados: {json.dumps(resultados)},
                segmentos: {json.dumps(segmentos)}
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.success) {{
                window.location.href = '/dashboard';
            }} else {{
                alert('Erro ao preparar edição');
            }}
        }});
    }}
    </script>
    '''
    return get_base_html(f"Resultados - {nome_simulacao}", content)

@app.route('/api/preparar_edicao', methods=['POST'])
def api_preparar_edicao():
    """API para preparar dados para edição"""
    try:
        dados = request.get_json()
        # Armazenar dados na sessão para o dashboard usar
        session['editar_simulacao_dados'] = dados
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/dashboard')
def dashboard():
    """Dashboard com opções de edição"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) as total, AVG(roi_total) as roi_medio, AVG(payback_total) as payback_medio FROM simulacoes')
        stats = cursor.fetchone()
        
        # Últimas simulações
        cursor.execute('''
        SELECT s.*, 
               (SELECT COUNT(*) FROM segmentos_simulacao ss WHERE ss.simulacao_id = s.id) as segmentos_ativos
        FROM simulacoes s 
        ORDER BY s.data_criacao DESC 
        LIMIT 15
        ''')
        simulacoes = cursor.fetchall()
        conn.close()
        
        # Verificar se há dados para edição na sessão
        dados_edicao = session.get('editar_simulacao_dados', {})
        mostrar_botao_edicao = bool(dados_edicao)
        
        # Tabela de simulações com botões de ação
        tabela_html = ""
        for s in simulacoes:
            data_formatada = datetime.strptime(s['data_criacao'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            
            # Extrair segmentos
            segmentos_detalhados = json.loads(s['segmentos_detalhados'] or '{}')
            segmentos_str = ", ".join([seg[:2] for seg in segmentos_detalhados.keys()])
            
            tabela_html += f'''
            <tr>
                <td>{data_formatada}</td>
                <td>
                    <strong>{s['nome'][:25]}{'...' if len(s['nome']) > 25 else ''}</strong>
                    <br><small class="text-muted">{s['segmentos_ativos']} segmentos</small>
                </td>
                <td>{s['total_alunos']}</td>
                <td>R$ {s['investimento_total']:,.0f}</td>
                <td><span class="badge {'bg-success' if s['roi_total'] > 100 else 'bg-warning'}">{s['roi_total']:.1f}%</span></td>
                <td>{s['payback_total']:.1f} meses</td>
                <td>
                    <div class="btn-group">
                        <a href="/ver_simulacao/{s['id']}" class="btn btn-sm btn-info" title="Ver">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="/simulacao/{s['id']}" class="btn btn-sm btn-warning" title="Editar">
                            <i class="fas fa-edit"></i>
                        </a>
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
                        <h3 class="mb-0"><i class="fas fa-tachometer-alt"></i> Dashboard - Gerencie suas Simulações</h3>
                    </div>
                    <div class="card-body">
                        {f'''
                        <div class="alert alert-warning alert-dismissible fade show" role="alert">
                            <h5><i class="fas fa-edit"></i> Pronto para editar!</h5>
                            <p>Você tem uma simulação pronta para edição. Clique no botão abaixo para continuar.</p>
                            <button type="button" class="btn btn-warning" onclick="continuarEdicao()">
                                <i class="fas fa-edit"></i> Continuar Edição
                            </button>
                            <button type="button" class="btn-close" onclick="cancelarEdicao()"></button>
                        </div>
                        ''' if mostrar_botao_edicao else ''}
                        
                        <!-- Estatísticas -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card bg-info text-white">
                                    <div class="card-body text-center">
                                        <h2>{stats['total'] or 0}</h2>
                                        <p>Total Simulações</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h2>{stats['roi_medio'] or 0:.1f}%</h2>
                                        <p>ROI Médio</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-warning text-white">
                                    <div class="card-body text-center">
                                        <h2>{stats['payback_medio'] or 0:.1f}</h2>
                                        <p>Payback Médio</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-secondary text-white">
                                    <div class="card-body text-center">
                                        <h2>{len(SEGMENTOS)}</h2>
                                        <p>Segmentos</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Histórico -->
                        <div class="card">
                            <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                                <h5 class="mb-0"><i class="fas fa-history"></i> Histórico de Simulações</h5>
                                <span class="badge bg-light text-dark">{len(simulacoes)} registros</span>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Data</th>
                                                <th>Nome / Segmentos</th>
                                                <th>Alunos</th>
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
                        
                        <!-- Ações Rápidas -->
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
                                <button class="btn btn-warning w-100" onclick="limparHistorico()">
                                    <i class="fas fa-broom"></i> Limpar Antigas
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function continuarEdicao() {{
            // Redirecionar para edição com os dados da sessão
            window.location.href = '/simulacao';
        }}
        
        function cancelarEdicao() {{
            // Limpar dados de edição
            fetch('/api/limpar_edicao', {{
                method: 'POST'
            }})
            .then(() => {{
                document.querySelector('.alert').remove();
            }});
        }}
        
        function excluirSimulacao(id) {{
            if (confirm('Tem certeza que deseja excluir esta simulação?\\n\\nEsta ação não pode ser desfeita.')) {{
                fetch(`/api/excluir_simulacao/${{id}}`, {{
                    method: 'DELETE'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('Simulação excluída com sucesso!');
                        window.location.reload();
                    }} else {{
                        alert('Erro ao excluir: ' + data.error);
                    }}
                }});
            }}
        }}
        
        function exportarTudo() {{
            alert('Exportando todas as simulações...');
            // Em uma versão futura, implementar exportação CSV/Excel
        }}
        
        function limparHistorico() {{
            if (confirm('Deseja limpar simulações com mais de 30 dias?\\n\\nEsta ação manterá apenas as simulações recentes.')) {{
                fetch('/api/limpar_historico', {{
                    method: 'POST'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert(data.message);
                        window.location.reload();
                    }} else {{
                        alert('Erro: ' + data.error);
                    }}
                }});
            }}
        }}
        </script>
        '''
        return get_base_html("Dashboard - Gerenciamento", content)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return redirect('/')

@app.route('/api/excluir_simulacao/<int:simulacao_id>', methods=['DELETE'])
def api_excluir_simulacao(simulacao_id):
    """API para excluir simulação"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Primeiro excluir os segmentos relacionados
        cursor.execute('DELETE FROM segmentos_simulacao WHERE simulacao_id = ?', (simulacao_id,))
        
        # Depois excluir a simulação
        cursor.execute('DELETE FROM simulacoes WHERE id = ?', (simulacao_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Simulação excluída'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/limpar_historico', methods=['POST'])
def api_limpar_historico():
    """API para limpar histórico antigo"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Excluir simulações com mais de 30 dias
        cursor.execute('''
        DELETE FROM simulacoes 
        WHERE date(data_criacao) < date('now', '-30 days')
        ''')
        
        excluidos = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{excluidos} simulações antigas foram removidas'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/limpar_edicao', methods=['POST'])
def api_limpar_edicao():
    """API para limpar dados de edição da sessão"""
    session.pop('editar_simulacao_dados', None)
    return jsonify({'success': True})

@app.route('/ver_simulacao/<int:id>')
def ver_simulacao(id):
    """Visualizar simulação específica"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (id,))
        simulacao = cursor.fetchone()
        
        if not simulacao:
            conn.close()
            return redirect('/dashboard')
        
        # Carregar dados da simulação
        dados_simulacao = json.loads(simulacao['dados'])
        segmentos_detalhados = json.loads(simulacao['segmentos_detalhados'] or '{}')
        
        conn.close()
        
        # Preparar dados para a sessão
        session['ultima_simulacao_avancada'] = {
            'dados_entrada': dados_simulacao.get('entrada', {}),
            'resultados': dados_simulacao.get('resultados', {}),
            'custos_detalhados': dados_simulacao.get('custos_detalhados', {}),
            'nome_simulacao': simulacao['nome']
        }
        
        return redirect('/resultado_avancado')
        
    except Exception as e:
        print(f"Erro ao visualizar simulação: {e}")
        return redirect('/dashboard')

if __name__ == '__main__':
    # Inicializar banco
    init_db()
    
    print("=" * 70)
    print("🚀 BUSINESS PLAN ESCOLAR - VERSÃO COM EDIÇÃO COMPLETA")
    print("=" * 70)
    print("✅ Criar novas simulações")
    print("✅ Editar simulações existentes")
    print("✅ Dashboard com histórico completo")
    print("✅ Excluir e gerenciar simulações")
    print("=" * 70)
    print("🔧 Funcionalidades de edição:")
    print("   • Editar qualquer valor de qualquer campo")
    print("   • Atualizar simulações existentes")
    print("   • Recalcular automaticamente")
    print("=" * 70)
    print("🌐 Acesse: http://localhost:5000")
    print("=" * 70)
    
    app.run(debug=True, port=5000, host='0.0.0.0')