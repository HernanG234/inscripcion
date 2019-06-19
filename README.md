### Inscripcion SASE 2019

Programa para procesar información del formulario de inscripción del SASE 2019.

Testeado en **Python 3.7.2**

## Requerimientos:

* Python 3.5+
* google-api-python-client==1.7.8
* google-auth==1.6.3
* google-auth-httplib2==0.0.3
* google-auth-oauthlib==0.3.0
* httplib2==0.12.3
* idna==2.8
* launch==0.4.0
* oauth2client==4.1.3
* oauthlib==3.0.1
* Pillow==6.0.0
* pyasn1==0.4.5
* pyasn1-modules==0.2.5
* PyPDF2==1.26.0
* qrcode==6.1
* requests==2.22.0
* requests-oauthlib==1.2.0
* rsa==4.0
* six==1.12.0
* uritemplate==3.0.0
* urllib3==1.25.2

**Extra:**

* pdflatex
* inkscape

## Funcionalidades:

* Autentificar login de Google.
* Descargar datos del formulario y acomodarlos en un diccionario para su uso: `get_formatted_ppl()`
* Generar códigos QR para acreditación con el uid: `generate_qrs()`
* Generar los gafetes, 8x10.5 y 16:9 para el celular: `generate_badges()`
* Cortar los gafetes para mostrar en el celular sin el resto de la hoja: `crop_badges()`
* Verificar si hay conflictos en workshops y tutoriales que se superpongan: `check_conflicts()`
* Enviar emails de confirmación/conflictos: `sendemail.SendMessage()`

## Ejecución:

```
$ git clone https://github.com/HernanG234/inscripcion.git
$ cd inscripcion
(Armar virtualenv o instalar todas las dependencias)
$ python main.py
```
