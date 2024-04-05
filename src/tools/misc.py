from langchain.tools import tool
import ast
from .wrapper import gtool, Session
from ..coords import Coords


@gtool("Decide")
def decide(decision: str) -> str:
    """
    This is a miscellaneous function that does nothing but note that a decision has been made.
    Use this to note different possibilities for the path of investigation.
    :param decision: The decision made. E.G. "The image is in America", "The image is in Europe"
    :return:
    """
    # TODO: perhaps add a critic?
    return "Decision noted"

@gtool("Plan Ahead")
def plan_ahead(plan: str) -> str:
    """
    This is a miscellaneous function that does nothing but note that a plan has been made.
    :param plan: The plan made. E.G. "I will use the streetview tool on the possible locations, then use StreetView Locate to narrow down the location"
    :return:
    """
    return "Plan noted"

@gtool("Add Clue")
def add_clue(clue: str, session: Session):
    """
    Add a clue to the global session.
    This should be a conclusion you have reached about the investigation that you are certain of
    :param clue: the clue to add
    :return:
    """
    session.add_conclusion(clue)
    return f"Clue added: {clue}"


def parse_lat_long_pairs(input_str):
    try:
        parsed = ast.literal_eval(input_str)
        if not all(isinstance(pair, tuple) and len(pair) == 2 and all(isinstance(coord, (float, int)) for coord in pair)
                   for pair in parsed):
            raise ValueError("Input string does not follow the required format: [(lat, long), (lat, long), ...]")
        return parsed
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"An error occurred while parsing the string: {e}")


@gtool("Save Coordinates")
def save_coords(coords: str, session: Session):
    """
    Given a set of coordinates, save them to a file so that you can use them in other tools
    :param coords: the coordinates to save, in the format [(lat, long), (lat, long), ...]
    :return:
    """
    parsed = parse_lat_long_pairs(coords)
    coords = Coords(parsed)
    return f"Coordinates saved: {coords.to_prompt(session, 'coords')}"
