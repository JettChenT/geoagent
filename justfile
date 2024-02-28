agent img_path='./images/anon/1.png':
    python -m src.agent {{img_path}}

agent-speedscope:
    sudo py-spy record --format speedscope -o ./trace/profile-$(date +"%Y%m%d%H%M%S").speedscope.json -- python -m src.agent

test-gpt:
    python -m src.connector.gptv

eval folder_path:
    python -m src.evaluation {{folder_path}}