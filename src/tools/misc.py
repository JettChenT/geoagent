from langchain.tools import tool


@tool("Decide")
def decide(decision: str) -> str:
    """
    This is a miscellaneous function that does nothing but note that a decision has been made.
    Use this to note different possibilities for the path of investigation.
    :param decision: The decision made. E.G. "The image is in America", "The image is in Europe"
    :return:
    """
    # TODO: perhaps add a critic?
    return "Decision noted"
