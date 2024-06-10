import base64

from openai import OpenAI

client = OpenAI(api_key="")

SYSTEM_MESSAGE = """Você é um especialista na análise de objetos e deve dizer a qual categoria o objeto em questão pertence.
As mensagens enviadas terão:
    - Uma imagem, com um objeto destacado
    - Uma lista de categorias possíveis
Você deve analisar a imagem e dizer a qual categoria o objeto destacado (com um retângulo) pertence, respondendo com o string correspondente ao "id" da categoria. Se não se encaixar em nenhuma, responda com o string Outros. Não escreva absolutamente nada além dessas coisas, nem mesmo aspas simples ou duplas."""


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class Category:
    def __init__(self, id, detail=None):
        self.id = id
        self.detail = detail

    def __str__(self):
        if self.detail:
            return str({"id": self.id, "detail": self.detail})
        return str({"id": self.id})


def detect_category(image_path, categories: list[Category]):
    system_message = SYSTEM_MESSAGE
    user_message = "\n".join(map(str, categories))
    base64_image = encode_image(image_path)
    messages = [
        {"role": "system", "content": system_message},
        {
            "role": "user",
            "content": (
                [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "low",
                        },
                    },
                ]
            ),
        },
    ]
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, temperature=0
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print(
        detect_category(
            "boxed_images/exemplar_box_1.png",
            [
                Category("Homem", "Um ser humano do sexo masculino"),
                Category("Mulher", "Um ser humano do sexo femenino"),
                Category(
                    "Garrafa",
                    "Um objeto cilíndrico de vidro ou plástico que armazena líquidos",
                ),
            ],
        )
    )
