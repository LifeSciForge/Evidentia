"""
Generate architecture diagram as PNG using graphviz
"""

from graphviz import Digraph

def create_architecture_diagram():
    dot = Digraph(comment='Evidentia Architecture', format='png')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue', fontname='Arial')
    
    # Title
    dot.node('title', 'EVIDENTIA - MSL Intelligence Platform', shape='box', fillcolor='#0055B8', fontcolor='white', fontsize='16', style='filled')
    
    # Input Layer
    dot.node('input', 'User Input\n(Hospital → Doctor → Drug → Indication)', fillcolor='#E8F1F8')
    dot.edge('title', 'input')
    
    # LangGraph Orchestration
    dot.node('langgraph', 'LangGraph Workflow\n(Sequential Agent Chain)', fillcolor='#FFE4B5')
    dot.edge('input', 'langgraph')
    
    # Six Agents
    agents = [
        ('agent1', 'Agent 1\nMarket Research', '#D4EDDA'),
        ('agent2', 'Agent 2\nPayer Intelligence', '#D4EDDA'),
        ('agent3', 'Agent 3\nCompetitor Analysis', '#D4EDDA'),
        ('agent4', 'Agent 4\nICP Definition', '#D4EDDA'),
        ('agent5', 'Agent 5\nMessaging & Positioning', '#D4EDDA'),
        ('agent6', 'Agent 6\nGTM Synthesis', '#D4EDDA'),
    ]
    
    for node_id, label, color in agents:
        dot.node(node_id, label, fillcolor=color)
        dot.edge('langgraph', node_id)
    
    # Agent Outputs
    outputs = [
        ('out1', 'Market Data\n(TAM, SAM, SOM)', '#E8F1F8'),
        ('out2', 'Payer Data\n(HTA, QALY, Pricing)', '#E8F1F8'),
        ('out3', 'Competitor Data\n(Market Share, Positioning)', '#E8F1F8'),
        ('out4', 'ICP Profile\n(Personas, Segments)', '#E8F1F8'),
        ('out5', 'Messaging\n(Positioning, Differentiators)', '#E8F1F8'),
        ('out6', 'GTM Strategy\n(Final Brief)', '#E8F1F8'),
    ]
    
    for i, (node_id, label, color) in enumerate(outputs):
        dot.node(node_id, label, fillcolor=color)
        dot.edge(agents[i][0], node_id)
    
    # Convergence
    dot.node('convergence', 'GTMState\n(Central State Machine)', fillcolor='#FFE4B5')
    for node_id, _, _ in outputs:
        dot.edge(node_id, 'convergence')
    
    # Streamlit UI
    dot.node('ui', 'Streamlit UI - 9 Tabs\n(Talking Points, Objections, Discovery,\nEvidence, Reimbursement, Competition,\nFinal Brief, Ask Evidentia, Download)', fillcolor='#87CEEB')
    dot.edge('convergence', 'ui')
    
    # External APIs
    dot.node('apis', 'External APIs\n(ClinicalTrials.gov, PubMed, Tavily)', fillcolor='#FFB6C6', shape='box')
    dot.edge('agent1', 'apis')
    dot.edge('agent2', 'apis')
    dot.edge('agent3', 'apis')
    
    # LLM
    dot.node('llm', 'Claude Sonnet 4\n(LLM Core)', fillcolor='#DDA0DD', shape='ellipse')
    for agent_id, _, _ in agents:
        dot.edge(agent_id, 'llm', style='dashed')
    
    # Output
    dot.node('output', 'MSL Intelligence Brief\n(JSON/CSV/PDF Download)', fillcolor='#90EE90')
    dot.edge('ui', 'output')
    
    # Render
    dot.render('docs/architecture_diagram', cleanup=True)
    print("✅ Architecture diagram created: docs/architecture_diagram.png")

if __name__ == '__main__':
    create_architecture_diagram()
