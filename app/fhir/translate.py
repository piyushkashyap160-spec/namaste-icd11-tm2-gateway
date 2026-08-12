from app.fhir.resources import (
    FHIRParameters,
    FHIRParameter,
    FHIRPart,
    FHIRCoding
)
from app.terminology.mapper import get_mapping_for_concept

DISCLAIMER_NOTE = "Algorithm-generated candidate mapping; not an official WHO/NAMASTE equivalence."

def process_fhir_translate(params: FHIRParameters) -> FHIRParameters:
    """
    Process FHIR R4 $translate operation.
    Extracts coding/code parameter, queries candidate mapping engine,
    and constructs standard FHIR ConceptMap $translate response.
    """
    code_to_translate = None
    system_of_code = None
    
    # Extract code from incoming parameters
    for param in params.parameter:
        if param.name in ("code", "coding") and param.valueCoding:
            code_to_translate = param.valueCoding.code
            system_of_code = param.valueCoding.system
            break
        elif param.name == "code" and param.valueCode:
            code_to_translate = param.valueCode
            break
        elif param.name == "concept" and param.valueCoding:
            code_to_translate = param.valueCoding.code
            system_of_code = param.valueCoding.system
            break

    if not code_to_translate:
        # Return unsuccessful FHIR Parameters
        return FHIRParameters(
            resourceType="Parameters",
            parameter=[
                FHIRParameter(name="result", valueBoolean=False),
                FHIRParameter(name="message", valueString="No code provided in request parameters"),
                FHIRParameter(name="disclaimer", valueString=DISCLAIMER_NOTE)
            ]
        )

    # Perform terminology candidate mapping
    mapping_res = get_mapping_for_concept(code_to_translate)

    if mapping_res.count == 0 or not mapping_res.matches:
        return FHIRParameters(
            resourceType="Parameters",
            parameter=[
                FHIRParameter(name="result", valueBoolean=False),
                FHIRParameter(name="message", valueString=f"No candidates found for code '{code_to_translate}'"),
                FHIRParameter(name="disclaimer", valueString=DISCLAIMER_NOTE)
            ]
        )

    # Take top candidate
    top_match = mapping_res.matches[0]

    response_parameters = [
        FHIRParameter(name="result", valueBoolean=True),
        FHIRParameter(
            name="match",
            part=[
                FHIRPart(name="equivalence", valueCode=top_match.equivalence),
                FHIRPart(
                    name="concept",
                    valueCoding=FHIRCoding(
                        system="http://id.who.int/icd/release/11/mms/tm2",
                        code=top_match.tm2_id,
                        display=top_match.tm2_title
                    )
                )
            ]
        ),
        FHIRParameter(name="disclaimer", valueString=DISCLAIMER_NOTE)
    ]

    return FHIRParameters(
        resourceType="Parameters",
        parameter=response_parameters
    )
