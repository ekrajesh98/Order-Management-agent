from pydantic import BaseModel, Field


class AnonymizerResult(BaseModel):
    """
    EngineResult represents the output of an anonymization run:
      - text: the fully anonymized string
    """

    text: str = Field("", description="The anonymized text")
