
from fasthtml.common import *

app = FastHTML()

@app.get("/")
def home():
    return Html(
        Head(
            Title("FastHTML no macOS")
        ),
        Body(
            Div(
                H2("Formulário"),

                Form(
                    Input(name="nome", placeholder="Nome"),
                    Br(), Br(),

                    Input(name="email", placeholder="Email", type="email"),
                    Br(), Br(),

                    Input(name="idade", placeholder="Idade", type="number"),
                    Br(), Br(),

                    Input(name="cidade", placeholder="Cidade"),
                    Br(), Br(),

                    Button("Enviar"),
                    method="post"
                ),

                style="""
                    width: 300px;
                    margin: 100px auto;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                """
            )
        )
    )

serve()
