# app_completo.py
from flask import Flask, render_template_string, request, jsonify, session, redirect
from datetime import datetime
import json
import math
import os
import sqlite3
import traceback

app = Flask(__name__)

# Configuração
app.config['SECRET_KEY'] = 'business_plan_escolar_seguro_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuração do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'database.db')

# Categorias de custos (simplificadas para facilitar)
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
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            alunos_atuais INTEGER,
            receita_alunos REAL,
            receita_nao_alunos REAL,
            quantidade_alunos INTEGER,
            quantidade_nao_alunos INTEGER,
            aumento_esperado INTEGER,
            nivel_escolar TEXT,
            investimento_total REAL,
            custo_mensal REAL,
            receita_mensal REAL,
            lucro_mensal REAL,
            payback REAL,
            roi REAL,
            dados TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado!")
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
    <style>
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .navbar-brand {{ font-weight: 700; }}
        .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .card-header {{ border-radius: 10px 10px 0 0 !important; }}
        .btn-primary {{ background-color: #4361ee; border-color: #4361ee; }}
        .btn-primary:hover {{ background-color: #3a0ca3; border-color: #3a0ca3; }}
        .custo-categoria {{ margin-bottom: 30px; }}
        .custo-item {{ margin-bottom: 15px; }}
        .sticky-summary {{ position: sticky; top: 20px; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        footer {{ background-color: #2c3e50; color: white; padding: 20px 0; margin-top: 40px; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line"></i> Business Plan Escolar
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Início</a>
                <a class="nav-link" href="/simulacao">Nova Simulação</a>
                <a class="nav-link" href="/dashboard">Dashboard</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {content}
    </div>

    <footer class="bg-dark text-white mt-5">
        <div class="container text-center">
            <p>Sistema de Business Plan para Escolas</p>
            <p class="mb-0">© 2024 - Desenvolvido com Python e Flask</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

@app.route('/')
def index():
    content = '''
    <div class="row">
        <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-primary text-white">
                <div class="card-body py-5">
                    <h1 class="display-4 mb-4">
                        <i class="fas fa-school"></i> Sistema de Business Plan Escolar
                    </h1>
                    <p class="lead mb-4">
                        Ferramenta completa para análise de custo-benefício de atividades extracurriculares.
                    </p>
                    <a href="/simulacao" class="btn btn-light btn-lg mt-4">
                        <i class="fas fa-play-circle"></i> Iniciar Nova Simulação
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="row mt-5">
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-calculator fa-3x text-primary mb-3"></i>
                    <h4>Cálculos Automáticos</h4>
                    <p>ROI, Payback, Lucro Mensal</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-money-bill-wave fa-3x text-success mb-3"></i>
                    <h4>Análise Financeira</h4>
                    <p>Receitas, Custos, Investimentos</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-chart-pie fa-3x text-info mb-3"></i>
                    <h4>Dashboard Completo</h4>
                    <p>Histórico de simulações</p>
                </div>
            </div>
        </div>
    </div>
    '''
    return get_base_html("Business Plan Escolar - Início", content)

@app.route('/simulacao')
def simulacao():
    """Página de simulação - TODOS os campos visíveis"""
    
    # Gerar campos de custo para cada categoria
    campos_custos = ""
    
    # 1. Infraestrutura
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-info text-white">
                <h5><i class="fas fa-tools"></i> Infraestrutura</h5>
            </div>
            <div class="card-body">
    '''
    
    for item in CATEGORIAS_CUSTOS['infraestrutura']:
        campo_id = f"infra_{item.replace(' ', '_').lower()}"
        campos_custos += f'''
        <div class="mb-3">
            <label class="form-label">{item}:</label>
            <div class="input-group">
                <span class="input-group-text">R$</span>
                <input type="number" class="form-control campo-custo" 
                       id="{campo_id}"
                       data-categoria="infraestrutura"
                       data-item="{item}"
                       value="0"
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
    
    # 2. Material
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h5><i class="fas fa-book"></i> Material e Equipamentos</h5>
            </div>
            <div class="card-body">
    '''
    
    for item in CATEGORIAS_CUSTOS['material']:
        campo_id = f"material_{item.replace(' ', '_').lower()}"
        campos_custos += f'''
        <div class="mb-3">
            <label class="form-label">{item}:</label>
            <div class="input-group">
                <span class="input-group-text">R$</span>
                <input type="number" class="form-control campo-custo" 
                       id="{campo_id}"
                       data-categoria="material"
                       data-item="{item}"
                       value="0"
                       min="0" 
                       step="50">
            </div>
        </div>
        '''
    
    campos_custos += '''
            </div>
        </div>
    </div>
    '''
    
    # 3. Marketing
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h5><i class="fas fa-bullhorn"></i> Marketing</h5>
            </div>
            <div class="card-body">
    '''
    
    for item in CATEGORIAS_CUSTOS['marketing']:
        campo_id = f"marketing_{item.replace(' ', '_').lower()}"
        campos_custos += f'''
        <div class="mb-3">
            <label class="form-label">{item}:</label>
            <div class="input-group">
                <span class="input-group-text">R$</span>
                <input type="number" class="form-control campo-custo" 
                       id="{campo_id}"
                       data-categoria="marketing"
                       data-item="{item}"
                       value="0"
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
    
    # 4. Recursos Humanos
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5><i class="fas fa-users"></i> Recursos Humanos</h5>
            </div>
            <div class="card-body">
    '''
    
    for item in CATEGORIAS_CUSTOS['recursos_humanos']:
        campo_id = f"rh_{item.replace(' ', '_').lower()}"
        campos_custos += f'''
        <div class="mb-3">
            <label class="form-label">{item}:</label>
            <div class="input-group">
                <span class="input-group-text">R$</span>
                <input type="number" class="form-control campo-custo" 
                       id="{campo_id}"
                       data-categoria="recursos_humanos"
                       data-item="{item}"
                       value="0"
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
    
    # 5. Custos Mensais
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-secondary text-white">
                <h5><i class="fas fa-dollar-sign"></i> Custos Mensais</h5>
            </div>
            <div class="card-body">
    '''
    
    for item in CATEGORIAS_CUSTOS['custos_mensais']:
        campo_id = f"mensal_{item.replace(' ', '_').lower()}"
        campos_custos += f'''
        <div class="mb-3">
            <label class="form-label">{item}:</label>
            <div class="input-group">
                <span class="input-group-text">R$</span>
                <input type="number" class="form-control campo-custo" 
                       id="{campo_id}"
                       data-categoria="custos_mensais"
                       data-item="{item}"
                       data-mensal="true"
                       value="0"
                       min="0" 
                       step="50">
            </div>
        </div>
        '''
    
    campos_custos += '''
            </div>
        </div>
    </div>
    '''
    
    # 6. Outros custos
    campos_custos += '''
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-dark text-white">
                <h5><i class="fas fa-plus-circle"></i> Outros Custos</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">Outros custos de investimento:</label>
                    <div class="input-group">
                        <span class="input-group-text">R$</span>
                        <input type="number" class="form-control campo-custo" 
                               id="outros_investimento"
                               data-categoria="outros"
                               data-item="Outros Investimentos"
                               value="0"
                               min="0" 
                               step="100">
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Outros custos mensais:</label>
                    <div class="input-group">
                        <span class="input-group-text">R$</span>
                        <input type="number" class="form-control campo-custo" 
                               id="outros_mensais"
                               data-categoria="outros"
                               data-item="Outros Mensais"
                               data-mensal="true"
                               value="0"
                               min="0" 
                               step="50">
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-calculator"></i> Nova Simulação</h3>
                </div>
                <div class="card-body">
                    <form id="simulacaoForm">
                        <div class="row">
                            <!-- Dados Básicos -->
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">Dados da Escola</h4>
                                
                                <div class="mb-3">
                                    <label class="form-label">Nível Escolar:</label>
                                    <select class="form-select" id="nivel_escolar">
                                        <option value="infantil">Educação Infantil</option>
                                        <option value="fundamental_i" selected>Ensino Fundamental I</option>
                                        <option value="fundamental_ii">Ensino Fundamental II</option>
                                        <option value="medio">Ensino Médio</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Número atual de alunos:</label>
                                    <input type="number" class="form-control" id="alunos_atuais" value="200">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Aumento esperado (%):</label>
                                    <input type="number" class="form-control" id="aumento_esperado" value="10" min="0" max="100">
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <h4 class="border-bottom pb-2 mb-3">Receitas</h4>
                                
                                <div class="mb-3">
                                    <label class="form-label">Receita por aluno (R$/mês):</label>
                                    <input type="number" class="form-control" id="receita_alunos" value="150">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Receita por não-aluno (R$/mês):</label>
                                    <input type="number" class="form-control" id="receita_nao_alunos" value="200">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Alunos participantes:</label>
                                    <input type="number" class="form-control" id="quantidade_alunos" value="80">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Não-alunos participantes:</label>
                                    <input type="number" class="form-control" id="quantidade_nao_alunos" value="30">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Todos os Campos de Custo -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <h4 class="border-bottom pb-2 mb-3">Custos Detalhados</h4>
                                <p class="text-muted">Preencha apenas os custos que se aplicam. Deixe como 0 os que não se aplicam.</p>
                                <div class="row">
                                    {campos_custos}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo e Botões -->
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <div class="sticky-summary">
                                    <h5>Resumo Financeiro</h5>
                                    <div id="resumo_custos">
                                        <p>Preencha os dados para ver o resumo</p>
                                    </div>
                                    <div class="mt-3">
                                        <button type="button" class="btn btn-primary w-100" onclick="calcularSimulacao()">
                                            <i class="fas fa-calculator"></i> Calcular Simulação
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary w-100 mt-2" onclick="resetForm()">
                                            <i class="fas fa-redo"></i> Limpar Formulário
                                        </button>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div id="resultado" style="display: none;">
                                    <!-- Resultados aparecerão aqui -->
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
        const campos = [
            'alunos_atuais', 'aumento_esperado', 'receita_alunos', 'receita_nao_alunos',
            'quantidade_alunos', 'quantidade_nao_alunos'
        ];
        
        campos.forEach(id => {{
            document.getElementById(id).addEventListener('input', atualizarResumo);
        }});
        
        // Eventos para campos de custo
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            campo.addEventListener('input', atualizarResumo);
        }});
        
        // Inicializar
        atualizarResumo();
    }});
    
    function atualizarResumo() {{
        // Dados básicos
        const receitaAlunos = parseFloat(document.getElementById('receita_alunos').value) || 0;
        const receitaNaoAlunos = parseFloat(document.getElementById('receita_nao_alunos').value) || 0;
        const qtdAlunos = parseInt(document.getElementById('quantidade_alunos').value) || 0;
        const qtdNaoAlunos = parseInt(document.getElementById('quantidade_nao_alunos').value) || 0;
        
        // Calcular receita
        const receitaMensal = (qtdAlunos * receitaAlunos) + (qtdNaoAlunos * receitaNaoAlunos);
        
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
        
        // Calcular lucro
        const lucroMensal = receitaMensal - custoMensalTotal;
        
        // Calcular indicadores
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
                    <td>Receita Mensal:</td>
                    <td class="text-end text-success">R$ ${{receitaMensal.toLocaleString('pt-BR')}}</td>
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
                    <td class="text-end text-success">${{roiPercentual.toFixed(1)}}%</td>
                </tr>
            </table>
            <div class="alert alert-info mt-3">
                <small><i class="fas fa-info-circle"></i> Preencha os dados e clique em "Calcular Simulação" para salvar</small>
            </div>
        `;
        
        document.getElementById('resumo_custos').innerHTML = resumoHTML;
    }}
    
    function resetForm() {{
        if (confirm('Limpar todos os dados?')) {{
            document.getElementById('simulacaoForm').reset();
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                campo.value = 0;
            }});
            atualizarResumo();
        }}
    }}
    
    async function calcularSimulacao() {{
        const btn = document.querySelector('button[onclick="calcularSimulacao()"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculando...';
        btn.disabled = true;
        
        try {{
            // Coletar dados
            const dados = {{
                alunos_atuais: parseInt(document.getElementById('alunos_atuais').value) || 0,
                receita_alunos: parseFloat(document.getElementById('receita_alunos').value) || 0,
                receita_nao_alunos: parseFloat(document.getElementById('receita_nao_alunos').value) || 0,
                quantidade_alunos: parseInt(document.getElementById('quantidade_alunos').value) || 0,
                quantidade_nao_alunos: parseInt(document.getElementById('quantidade_nao_alunos').value) || 0,
                aumento_esperado: parseInt(document.getElementById('aumento_esperado').value) || 0,
                nivel_escolar: document.getElementById('nivel_escolar').value
            }};
            
            // Coletar custos
            const custosDetalhados = {{}};
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                const categoria = campo.getAttribute('data-categoria');
                const item = campo.getAttribute('data-item');
                const valor = parseFloat(campo.value) || 0;
                const isMensal = campo.hasAttribute('data-mensal');
                
                if (!custosDetalhados[categoria]) {{
                    custosDetalhados[categoria] = {{}};
                }}
                custosDetalhados[categoria][item] = {{
                    valor: valor,
                    mensal: isMensal
                }};
            }});
            
            dados.custos_detalhados = custosDetalhados;
            
            console.log('Enviando dados:', dados);
            
            // Enviar para o servidor
            const response = await fetch('/api/calcular', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(dados)
            }});
            
            if (!response.ok) {{
                throw new Error(`Erro HTTP ${{response.status}}`);
            }}
            
            const resultados = await response.json();
            console.log('Resultados:', resultados);
            
            // Mostrar resultados
            mostrarResultados(resultados);
            
        }} catch (error) {{
            console.error('Erro:', error);
            alert('Erro ao calcular: ' + error.message);
        }} finally {{
            btn.innerHTML = originalText;
            btn.disabled = false;
        }}
    }}
    
    function mostrarResultados(resultados) {{
        const divResultado = document.getElementById('resultado');
        
        const html = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-check-circle"></i> Simulação Calculada!</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <p>Simulação salva com sucesso! Redirecionando para os resultados...</p>
                    </div>
                    <p>Em instantes você será redirecionado para ver a análise completa.</p>
                </div>
            </div>
        `;
        
        divResultado.innerHTML = html;
        divResultado.style.display = 'block';
        
        // Redirecionar após 2 segundos
        setTimeout(() => {{
            window.location.href = '/resultado';
        }}, 2000);
    }}
    </script>
    '''
    return get_base_html("Nova Simulação", content)

@app.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API para cálculo - SIMPLES E FUNCIONAL"""
    try:
        print("=" * 50)
        print("API /api/calcular CHAMADA")
        print("=" * 50)
        
        # Obter dados
        dados = request.get_json()
        if not dados:
            return jsonify({'error': 'Nenhum dado recebido'}), 400
        
        print(f"Dados recebidos: {json.dumps(dados, indent=2)}")
        
        # Extrair valores com segurança
        receita_alunos = float(dados.get('receita_alunos', 0) or 0)
        receita_nao_alunos = float(dados.get('receita_nao_alunos', 0) or 0)
        qtd_alunos = int(dados.get('quantidade_alunos', 0) or 0)
        qtd_nao_alunos = int(dados.get('quantidade_nao_alunos', 0) or 0)
        
        # Calcular receita
        receita_mensal = (qtd_alunos * receita_alunos) + (qtd_nao_alunos * receita_nao_alunos)
        
        # Calcular custos
        investimento_total = 0
        custo_mensal = 0
        
        custos_detalhados = dados.get('custos_detalhados', {})
        for categoria, itens in custos_detalhados.items():
            for item, info in itens.items():
                valor = float(info.get('valor', 0) or 0)
                if info.get('mensal'):
                    custo_mensal += valor
                else:
                    investimento_total += valor
        
        # Calcular lucro
        lucro_mensal = receita_mensal - custo_mensal
        
        # Calcular indicadores
        payback_meses = 0
        roi_percentual = 0
        
        if lucro_mensal > 0 and investimento_total > 0:
            payback_meses = investimento_total / lucro_mensal
            roi_percentual = (lucro_mensal * 12 / investimento_total) * 100
        
        # Criar resultado
        resultados = {
            'receita_mensal': receita_mensal,
            'investimento_total': investimento_total,
            'custo_mensal': custo_mensal,
            'lucro_mensal': lucro_mensal,
            'payback_meses': payback_meses,
            'roi_percentual': roi_percentual,
            'qtd_alunos': qtd_alunos,
            'qtd_nao_alunos': qtd_nao_alunos,
            'total_participantes': qtd_alunos + qtd_nao_alunos
        }
        
        print(f"Resultados calculados: {json.dumps(resultados, indent=2)}")
        
        # Salvar na sessão
        session['ultima_simulacao'] = {
            'dados_entrada': dados,
            'resultados': resultados,
            'custos_detalhados': custos_detalhados
        }
        
        # Salvar no banco
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO simulacoes (
                nome, data_criacao, alunos_atuais, receita_alunos, receita_nao_alunos,
                quantidade_alunos, quantidade_nao_alunos, aumento_esperado, nivel_escolar,
                investimento_total, custo_mensal, receita_mensal, lucro_mensal,
                payback, roi, dados
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"Simulação {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                int(dados.get('alunos_atuais', 0) or 0),
                receita_alunos,
                receita_nao_alunos,
                qtd_alunos,
                qtd_nao_alunos,
                int(dados.get('aumento_esperado', 0) or 0),
                dados.get('nivel_escolar', 'fundamental_i'),
                investimento_total,
                custo_mensal,
                receita_mensal,
                lucro_mensal,
                payback_meses,
                roi_percentual,
                json.dumps({
                    'entrada': dados,
                    'resultados': resultados,
                    'custos_detalhados': custos_detalhados
                })
            ))
            
            conn.commit()
            conn.close()
            print("✅ Simulação salva no banco!")
            
        except Exception as e:
            print(f"⚠️ Não foi possível salvar no banco: {e}")
        
        return jsonify(resultados)
        
    except Exception as e:
        print(f"❌ ERRO NA API: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'Erro interno no cálculo'
        }), 500

@app.route('/resultado')
def resultado():
    """Página de resultados"""
    if 'ultima_simulacao' not in session:
        return redirect('/simulacao')
    
    dados = session['ultima_simulacao']
    resultados = dados['resultados']
    
    content = f'''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card shadow">
                <div class="card-header bg-success text-white">
                    <h3 class="mb-0"><i class="fas fa-chart-line"></i> Resultados da Simulação</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-success">
                        <h4><i class="fas fa-trophy"></i> Análise Financeira Completa</h4>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="mb-0">Indicadores Financeiros</h5>
                                </div>
                                <div class="card-body">
                                    <table class="table table-bordered">
                                        <tr>
                                            <th>Receita Mensal:</th>
                                            <td class="text-success">R$ {resultados.get('receita_mensal', 0):,.2f}</td>
                                        </tr>
                                        <tr>
                                            <th>Investimento Total:</th>
                                            <td class="text-warning">R$ {resultados.get('investimento_total', 0):,.2f}</td>
                                        </tr>
                                        <tr>
                                            <th>Custos Mensais:</th>
                                            <td>R$ {resultados.get('custo_mensal', 0):,.2f}</td>
                                        </tr>
                                        <tr class="table-success">
                                            <th><strong>Lucro Mensal:</strong></th>
                                            <td><strong>R$ {resultados.get('lucro_mensal', 0):,.2f}</strong></td>
                                        </tr>
                                        <tr>
                                            <th>Payback:</th>
                                            <td>{resultados.get('payback_meses', 0):.1f} meses</td>
                                        </tr>
                                        <tr>
                                            <th>ROI Anual:</th>
                                            <td class="text-success"><strong>{resultados.get('roi_percentual', 0):.1f}%</strong></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card mb-3">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0">Participantes</h5>
                                </div>
                                <div class="card-body text-center">
                                    <h1 class="display-1 text-primary">{resultados.get('total_participantes', 0)}</h1>
                                    <p class="lead">Total de Participantes</p>
                                    <div class="row">
                                        <div class="col-6">
                                            <div class="alert alert-info">
                                                <h4>{resultados.get('qtd_alunos', 0)}</h4>
                                                <p>Alunos</p>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="alert alert-secondary">
                                                <h4>{resultados.get('qtd_nao_alunos', 0)}</h4>
                                                <p>Não-Alunos</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header bg-warning text-dark">
                                    <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Recomendações</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert { 'alert-success' if resultados.get('roi_percentual', 0) > 100 else 'alert-warning' }">
                                        <h5>
                                            <i class="fas {'fa-check-circle' if resultados.get('roi_percentual', 0) > 100 else 'fa-exclamation-triangle'}"></i>
                                            Viabilidade: {'ALTA' if resultados.get('roi_percentual', 0) > 100 else 'MODERADA'}
                                        </h5>
                                        <p>
                                            ROI de {resultados.get('roi_percentual', 0):.1f}% indica 
                                            {'um excelente retorno sobre o investimento' if resultados.get('roi_percentual', 0) > 100 else 'um retorno satisfatório'}.
                                        </p>
                                    </div>
                                    
                                    <div class="text-center">
                                        <a href="/simulacao" class="btn btn-primary me-2">
                                            <i class="fas fa-redo"></i> Nova Simulação
                                        </a>
                                        <a href="/dashboard" class="btn btn-success me-2">
                                            <i class="fas fa-tachometer-alt"></i> Dashboard
                                        </a>
                                        <button class="btn btn-info" onclick="window.print()">
                                            <i class="fas fa-print"></i> Imprimir
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
    '''
    return get_base_html("Resultados da Simulação", content)

@app.route('/dashboard')
def dashboard():
    """Dashboard com histórico"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes ORDER BY data_criacao DESC LIMIT 10')
        simulacoes = cursor.fetchall()
        conn.close()
        
        # Criar tabela
        tabela_html = ""
        for s in simulacoes:
            tabela_html += f'''
            <tr>
                <td>{s['data_criacao'][:10]}</td>
                <td>{s['nome']}</td>
                <td>{s['nivel_escolar'].replace('_', ' ').title()}</td>
                <td>{s['alunos_atuais']}</td>
                <td>{s['quantidade_alunos'] + s['quantidade_nao_alunos']}</td>
                <td>R$ {s['investimento_total']:,.0f}</td>
                <td><span class="badge {'bg-success' if s['roi'] > 100 else 'bg-warning'}">{s['roi']:.1f}%</span></td>
                <td>{s['payback']:.1f} meses</td>
            </tr>
            '''
        
        if not simulacoes:
            tabela_html = '''
            <tr>
                <td colspan="8" class="text-center py-4">
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
                        <h3 class="mb-0"><i class="fas fa-tachometer-alt"></i> Dashboard</h3>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <h5><i class="fas fa-history"></i> Histórico de Simulações</h5>
                            <p>Últimas 10 simulações realizadas</p>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Data</th>
                                        <th>Nome</th>
                                        <th>Nível</th>
                                        <th>Alunos</th>
                                        <th>Participantes</th>
                                        <th>Investimento</th>
                                        <th>ROI</th>
                                        <th>Payback</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tabela_html}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="text-center mt-4">
                            <a href="/simulacao" class="btn btn-primary">
                                <i class="fas fa-plus-circle"></i> Nova Simulação
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
        return get_base_html("Dashboard", content)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    content = '''
    <div class="container text-center py-5">
        <h1 class="display-1 text-muted">404</h1>
        <h2 class="mb-4">Página não encontrada</h2>
        <a href="/" class="btn btn-primary">Voltar ao Início</a>
    </div>
    '''
    return get_base_html("Página não encontrada", content), 404

@app.errorhandler(500)
def internal_server_error(e):
    content = '''
    <div class="container text-center py-5">
        <h1 class="display-1 text-danger">500</h1>
        <h2 class="mb-4">Erro interno do servidor</h2>
        <a href="/" class="btn btn-primary">Voltar ao Início</a>
    </div>
    '''
    return get_base_html("Erro Interno", content), 500

if __name__ == '__main__':
    # Inicializar banco
    init_db()
    
    print("=" * 60)
    print("🚀 SISTEMA DE BUSINESS PLAN ESCOLAR")
    print("=" * 60)
    print("✅ Versão COMPLETA e FUNCIONAL")
    print("✅ TODOS os campos visíveis")
    print("✅ Nenhum campo obrigatório")
    print("✅ Cálculos automáticos")
    print("=" * 60)
    print("🌐 Acesse: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
