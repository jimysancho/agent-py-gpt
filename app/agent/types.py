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
    
    question: str
    reasoning: str
    question_type: str
    subject: Set[str | None]
    valid: Optional[bool] = False
    
    @model_validator(mode='before')
    def coherence_between_question_type_and_length_of_subjects(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        subject, question_type = values.get('subject'), values.get('question_type')
        if (len(subject) <= 1 and question_type != 'simple') or (len(subject) > 1 and question_type != 'complex'):
            values['valid'] = False
        else:
            values['valid'] = True
        return values    
