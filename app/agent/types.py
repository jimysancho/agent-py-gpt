import enum
from pydantic import BaseModel, model_validator

from typing import (Optional,
                    Set, 
                    Dict, 
                    Any)

class QuestionType(enum.Enum):

    SIMPLE = "SIMPLE"
    COMPLEX = "COMPLEX"

class ContextType(enum.Enum):
    
    PARTICULAR = "PARTICULAR"
    GENERAL = "GENERAL"
    

class Output(BaseModel):
    
    query: str
    reasoning: str
    question_type: str
    subject: Set[str | None]
    valid: Optional[bool] = True
    
    @model_validator(mode='before')
    def coherence_between_question_type_and_length_of_subjects(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        subject, question_type = values.get('subject'), values.get('question_type')
        if question_type not in ('simple', 'complex'):
            return values
        if (len(subject) <= 1 and question_type != 'simple') or (len(subject) > 1 and question_type != 'complex'):
            values['valid'] = False
        return values    
