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

    response_parameters = [
        FHIRParameter(name="result", valueBoolean=True),
    ]

    for match in mapping_res.matches:
        response_parameters.append(
            FHIRParameter(
                name="match",
                part=[
                    FHIRPart(name="equivalence", valueCode=match.equivalence),
                    FHIRPart(name="confidence", valueCode=match.confidence),
                    FHIRPart(
                        name="concept",
                        valueCoding=FHIRCoding(
                            system=match.tm2_system,
                            version=match.tm2_version,
                            code=match.tm2_code,
                            display=match.tm2_title
                        )
                    )
                ]
            )
        )

    response_parameters.append(FHIRParameter(name="disclaimer", valueString=DISCLAIMER_NOTE))

    return FHIRParameters(
        resourceType="Parameters",
        parameter=response_parameters
    )
