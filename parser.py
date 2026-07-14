from pydantic import BaseModel
from typing import Literal


class Response(BaseModel):
    answer : str
    
class Validater(BaseModel):
    attacker_valid : bool
    defender_valid : bool
    winner : Literal["attacker","defender","null"]
    reason : str