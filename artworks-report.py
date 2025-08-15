import smtplib
import ssl
import os
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import argparse


parser = argparse.ArgumentParser(
    description="Programa de consulta del instituto de arte."
)
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default="a",
    help="Campos consultar, puede ser en forma de lista o archivo .yml",
)
parser.add_argument(
    "-o",
    "--out",
    default="json",
    help="Tipo de archivo con la consulta, pdf o json",
)
parser.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    help="No envía correos; solo genera salidas",
)
"""
def opciones_busqueda(lista_busqueda) :
    os.system("curl https://api.artic.edu/api/v1/artworks | jq '.data[0] | keys' > opciones.txt ")
    with open('opciones.txt', 'r') as f:
        opciones_disponibles = f.readline()
    for i in range ()
    print(opciones_disponibles)"""


def info_galeria():

    # Extrae la cantidad de obras de arte en la galería

    os.system(
        "curl https://api.artic.edu/api/v1/artworks | jq '.data | length' > longitud.txt"
    )
    with open("longitud.txt", "r") as f:
        longitud = int(f.read())

    # Extrae que clase de información se conoce de cada obra

    os.system(
        "curl https://api.artic.edu/api/v1/artworks | jq '.data[0] | keys' | jq '.[]' > parametros_busqueda.txt"
    )
    with open("parametros_busqueda.txt", "r") as f:
        parametros_busqueda = f.read()
    parametros_busqueda = parametros_busqueda.replace('"', "").split("\n")

    return parametros_busqueda, longitud


def depura_busqueda(peticion_usuario: list, campos_disponibles) -> list:
    contador_parametros_eliminar = []
    for i in range(0, len(peticion_usuario), 1):
        if (peticion_usuario[i] in campos_disponibles) == False:
            contador_parametros_eliminar.append(i)
    contador_parametros_eliminar.reverse()

    for i in contador_parametros_eliminar:
        peticion_usuario.pop(i)

    return peticion_usuario


def ejecuta_consulta(numero_obras: int, parametros_busqueda: list) -> dict:
    resultado_consulta = {}

    for i in parametros_busqueda:
        resultado_consulta[i] = []
        for ii in range(0, numero_obras, 1):
            os.system(
                f"curl https://api.artic.edu/api/v1/artworks | jq '.data[{ii}].{i}' > consulta.txt"
            )
            with open("consulta.txt", "r") as f:
                resultado_consulta_raw = (
                    f.read().replace("\n", "").replace('"', "")
                )
                resultado_consulta[i].append(resultado_consulta_raw)

    return resultado_consulta


def generar_archivo(tipo: str, nombre_archivo: str, contenido: any) -> str:
    archivo = f"{nombre_archivo}.{tipo}"
    with open(archivo, "w") as f:
        caracteres = f.write(f"{contenido}")

    return archivo


def envia_archivo(destino: str, nombre_archivo: str):
    # Se establace conexión con el servidor para mandar un mail
    port = 465
    clave = "dmun fzvl rqem vihp"
    origen = "kevinarroyave31@gmail.com"
    context = ssl.create_default_context()
    # Se procede con la creación del mensaje
    asunto = "Consulta galería de arte"
    cuerpo = "Este es un mensaje generado automáticament por Kevin Arroyave a traves de un script"
    msg = MIMEMultipart()
    msg["From"] = origen
    msg["To"] = destino
    msg["Subject"] = asunto
    body = MIMEText(cuerpo, "plain")
    msg.attach(body)

    with open(nombre_archivo, "r") as f:
        adjunto = MIMEApplication(f.read(), Name=nombre_archivo)
        adjunto["Contenet-Disposition"] = (
            f'adjunto; nombre_archivo = "{nombre_archivo}"'
        )

    msg.attach(adjunto)
    # Se envia el archivo
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(origen, clave)
        server.send_message(msg, origen, destino)


def extrae_yml(direccion: str) -> dict:
    try:
        with open(direccion, "r") as f:
            info = yaml.safe_load(f)
    except Exception as e:
        return 0
    else:
        return info


def extrae_str(str_procesar: str) -> dict:
    list_proceso = str_procesar.split(" ")
    print(f"la lista obtenida de momento es:\n{list_proceso}\n")
    dict_proceso = {}
    for i in list_proceso:
        par_clave_valor = i.split(":")
        print(f"El par a procesar es: {par_clave_valor} \n")
        if (par_clave_valor[1][0] == "[") and (par_clave_valor[1][-1] == "]"):

            par_clave_valor[1] = par_clave_valor[1].removeprefix("[")
            par_clave_valor[1] = par_clave_valor[1].removesuffix("]")
            par_clave_valor[1] = par_clave_valor[1].split(",")

        elif par_clave_valor[1].isnumeric():

            par_clave_valor[1] = int(par_clave_valor[1])

        dict_proceso[par_clave_valor[0]] = par_clave_valor[1]
    print("Conversion de str a dict completada")
    return dict_proceso


def ordena_configuracion(dict_config: dict) -> any:

    return (
        dict_config["fields"],
        dict_config["name"],
        dict_config["max_items"],
        dict_config["recipients"],
    )


if __name__ == "__main__":

    args = parser.parse_args()
    tipo_archivo = args.out
    print(f"\n\n\nlos argumentos capturados son: {args}\n\n\n")

    if (args.config.endswith((".yml", ".yaml"))) == True:
        configuracion = extrae_yml(args.config)
    else:
        configuracion = extrae_str(args.config)

    if type(configuracion) == dict:
        print(configuracion)
        try:
            lista_busqueda_usuario, nombre, max, email_destino = (
                ordena_configuracion(configuracion)
            )
        except Exception:
            print("Algo a salido mal al acceder a los datos de configuracion")
        else:

            parametros_disponibles, cantidad_obras = info_galeria()
            busqueda_final = depura_busqueda(
                lista_busqueda_usuario, parametros_disponibles
            )
            consulta = ejecuta_consulta(cantidad_obras, busqueda_final)
            archivo_generado = generar_archivo(tipo_archivo, nombre, consulta)

            # Se envía el archivo
            if (args.dry_run == True) and (len(email_destino) > 0):
                for email in email_destino:
                    envia_archivo(email, archivo_generado)
            elif not (len(email_destino) > 0):
                print("No has suministrado una dirreción de correo")
            elif args.dry_run == False:
                print("No has habilitado el envio de mails")
    else:
        print("Algo a salido mal con la lectura de la configuracion")

# Una consulta como base :

#  python3 Galeria_arte.py -o ""name":"peace-art" "fields":["id","title","artist_title","date_display"] "max_items":25 "search":"peace" "recipients":[""]" -o json -d True
