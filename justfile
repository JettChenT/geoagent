agent:
    python -m src.agent

agent-speedscope:
    sudo py-spy record --format speedscope -o ./trace/profile-$(date +"%Y%m%d%H%M%S").speedscope.json -- python -m src.agent

test-gpt:
    python -m src.connector.gptv