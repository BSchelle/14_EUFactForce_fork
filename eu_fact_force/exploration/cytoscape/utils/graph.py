from .colors import AppColors

elements = [
    # Nodes
    {"data": {"id": "1", "label": "Paper A", "type": "paper"}},
    {"data": {"id": "2", "label": "Paper B", "type": "paper"}},
    {"data": {"id": "3", "label": "Paper C", "type": "paper"}},
    {"data": {"id": "4", "label": "Journal A", "type": "journal"}},
    {"data": {"id": "5", "label": "Journal B", "type": "journal"}},
    # Edges
    {"data": {"source": "1", "target": "4"}},
    {"data": {"source": "2", "target": "4"}},
    {"data": {"source": "3", "target": "5"}},
]

stylesheet = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "text-valign": "center",
            "color": "black",
        },
    },
    {
        "selector": 'node[type="paper"]',
        "style": {
            "background-color": AppColors.blue,
        },
    },
    {
        "selector": 'node[type="journal"]',
        "style": {
            "background-color": AppColors.green,
        },
    },
    {
        "selector": "edge",
        "style": {
            "width": 2,
            "line-color": "black",
        },
    },
]
