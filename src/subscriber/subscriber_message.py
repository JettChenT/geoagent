from enum import Enum

class SubscriberMessageType(Enum):
    GlobalInfoSet = "global_info_set"
    SetSessionInfoKey = "set_session_info_key"
    SetSessionInfo = "set_session_info"
    SetCurrentSession = "set_current_session"
    AddNode = "add_node"
    RootNode = "root_node"
    
