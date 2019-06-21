from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import qrcode
import subprocess
import PyPDF2
import re
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.mime.base import MIMEBase
from email import encoders
import sendemail
import itertools

# If modifying these scopes, delete the file token.pickle.
SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly https://www.googleapis.com/auth/gmail.send"

# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
# SAMPLE_SPREADSHEET_ID = '1VzMaGzQWcD66zX5gA4wWXOqE-Nbfx0oz_mIvbbAe_cc'
SAMPLE_SPREADSHEET_ID = '14Ey6KMIbf3rl_HUxho7PNRzB5r1RpV6g4H_rj6_Kst8'
# SAMPLE_RANGE_NAME = 'Class Data!A2:F'
# SAMPLE_RANGE_NAME = 'insc!A1:Z'
SAMPLE_RANGE_NAME = 'Respuestas de formulario 1!A1:Z'

# Columns for reference
columns = ["Marca temporal", "Dirección de correo electrónico", "Apellido", "Nombre/s", "DNI", "Pais de Residencia", "Provincia de residencia", "Estado Laboral", "Estado Académico", "Institucion / Empresa", "Area de Trabajo / Investigacion", "Deseo inscribirme a (día 1):", "Cuando haya revisado la validez de su selección, marque la siguiente casilla", "Deseo inscribirme a (día 2):", "Cuando haya revisado la validez de su selección, marque la siguiente casilla", "Deseo inscribirme a (día 3):", "Cierre SASE 2019: Viernes 19/07, 15:30 - 17:30", "Para finalizar, reingrese su correo electrónico", "Cuando haya revisado la validez de su selección, marque la siguiente casilla", "¿Desea asistir al CASE?"]

def generate_qrs(ppl):
    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=14, border=4)

    for uid, values in ppl.items():
        print(values)
        filename = 'badge/qrs/'+uid+'.png'
        qr.add_data(uid)
        qr.make(fit=True)
        img = qr.make_image()
        with open(filename, 'wb') as f:
            img.save(f)

def generate_badges(ppl):
    with open("badge/badge-mobile.tex", "rt") as fin:
        content = fin.read()

        for uid, values in ppl.items():
            patterns = { 
                    'ReplaceWithName'     : values['Nombre/s']+' '+values['Apellido'],
                    'ReplaceWithUni'      : values['Institucion / Empresa'],
                    'ReplaceWithCondition': get_profession(values['Estado Laboral']),
                    'QRPath'              : 'qrs/'+uid+'.png',
                   }

            with open("badge/out.tex", "w") as fout:
                newcontent = content
                for i,j in patterns.items():
                    newcontent = newcontent.replace(i,j)
                fout.write(newcontent)
            cmd = 'pdflatex -output-directory badges out.tex'
            cmd2 = 'cp badges/out.pdf badges/{}-m.pdf'.format(uid)
            cmd3 = 'rm badges/out.*'
            print (cmd.split())
            result = subprocess.run(cmd.split(), check=True, text=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result2 = subprocess.run(cmd2.split(), check=True, text=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result3 = subprocess.run(cmd3, shell=True, check=True, text=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and result2.returncode == 0 and result3.returncode == 0:
                print ("Badge Created for: ", uid)
                ppl[uid]['badge-m']='badge/badges/'+uid+'-m.pdf'
            elif result.stderr or result2.stderr or result3.stderr:
                    Style.error('Badge creation failed: ')
                    print(result.stderr, result2.stderr, result3.stderr)

    with open("badge/badge.tex", "rt") as fin:
        content = fin.read()

        for uid, values in ppl.items():
            patterns = { 
                    'ReplaceWithName'     : values['Nombre/s']+' '+values['Apellido'],
                    'ReplaceWithUni'      : values['Institucion / Empresa'],
                    'ReplaceWithCondition': get_profession(values['Estado Laboral']),
                    'QRPath'              : 'qrs/'+uid+'.png',
                   }

            with open("badge/out.tex", "w") as fout:
                newcontent = content
                for i,j in patterns.items():
                    newcontent = newcontent.replace(i,j)
                fout.write(newcontent)
            cmd = 'pdflatex -output-directory badges out.tex'
            cmd2 = 'cp badges/out.pdf badges/{}.pdf'.format(uid)
            cmd3 = 'rm badges/out.*'
            print (cmd.split())
            result = subprocess.run(cmd.split(), check=True, universal_newlines=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result2 = subprocess.run(cmd2.split(), check=True, universal_newlines=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result3 = subprocess.run(cmd3, shell=True, check=True, universal_newlines=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and result2.returncode == 0 and result3.returncode == 0:
                print ("Badge Created for: ", uid)
                ppl[uid]['badge']='badge/badges/'+uid+'.pdf'
            elif result.stderr or result2.stderr or result3.stderr:
                    Style.error('Badge creation failed: ')
                    print(result.stderr, result2.stderr, result3.stderr)


def crop_badges(ppl):
    for uid, values in ppl.items():
        cmd = 'pdftocairo -svg badges/{}-m.pdf badges/{}-m.svg'.format(uid,uid)
        cmd2 = 'inkscape -z -D -f badges/{}-m.svg -A badges/{}-m-cropped.pdf'.format(uid,uid)
        result = subprocess.run(cmd.split(), check=True, universal_newlines=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result2 = subprocess.run(cmd2.split(), check=True, universal_newlines=True, cwd='badge')#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0 and result2.returncode == 0:
            print ("Badge Cropped for: ", uid)
            ppl[uid]['badge-m-cropped']='badge/badges/'+uid+'-m-cropped.pdf'
        elif result.stderr or result2.stderr:
                 Style.error('Badge cropping failed: ')
                 print(result.stderr, result2.stderr)

def get_profession(csvstring):
    if re.match("Estudiante", csvstring):
        return "Estudiante"
    elif re.match("Profesor", csvstring):
        return "Profesor"
    elif re.match("Profesional", csvstring):
        return "Profesional"
    else:
        return ""

def get_formatted_ppl(keys, values):
    ppl = {}
    for row in values:
        person = {}
        print (len(keys))
        for idx in range(0, len(keys)):
           print(idx)
           try:
               if re.match("Deseo inscrbirme a", keys[idx]) != None:
                   person[keys[idx]] = re.split(",[ ]*(?=Workshop|Tutorial)", row[idx]) # Find ", {Workshop,Tutorial}" string, return a list.
               else:
                   person[keys[idx]] = row[idx]
           except IndexError:
               person[keys[idx]] = "__place_holder__"
        ppl[row[4]] = person

    return ppl

'''
Día 1:
Bloque A, excluye a: B, C, D, E
Bloque B, excluye a: A, D, F
Bloque C, excluye a: A
Bloque D, excluye a: A, B
Bloque E, excluye a: A, B
'''
dia1 = {}
dia1["A"] = ['A', 'B', 'C', 'D', 'E']
dia1["B"] = ['A', 'B', 'D', 'F']
dia1["C"] = ['A', 'C']
dia1["D"] = ['A', 'B', 'D']
dia1["E"] = ['A', 'B', 'E']
'''
Día 2:
Bloque A, excluye a: B, C, D, E, F, G, H
Bloque B, excluye a: A, E, F
Bloque C, excluye a: A, G
Bloque D, excluye a: A, H
Bloque E, excluye a: A, B
Bloque F, excluye a: A, B
Bloque G, excluye a: A, C
Bloque H, excluye a: A, D
'''
dia2 = {}
dia2["A"] = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
dia2["B"] = ['A', 'B', 'E', 'F']
dia2["C"] = ['A', 'C', 'G']
dia2["D"] = ['A', 'D', 'H']
dia2["E"] = ['A', 'B', 'E']
dia2["F"] = ['A', 'B', 'F']
dia2["G"] = ['A', 'C', 'G']
dia2["H"] = ['A', 'D', 'H']
'''
Día 3:
Bloque A, excluye a: B, C, D, E, F
Bloque B, excluye a: A, D, E
Bloque C, excluye a: A, F
Bloque D, excluye a: A, B
Bloque E, excluye a: A, B
Bloque F, excluye a: A, C
'''
dia3 = {}
dia3["A"] = ['A', 'B', 'C', 'D', 'E', 'F']
dia3["B"] = ['A', 'B', 'D', 'E']
dia3["C"] = ['A', 'C', 'F']
dia3["D"] = ['A', 'B', 'D']
dia3["E"] = ['A', 'B', 'E']
dia3["F"] = ['A', 'C', 'F']

def __check_conflicts(blocks, dia, ppl, uid, n):
    for c, block in enumerate(blocks):
        rest = [x for i,x in enumerate(blocks) if i!=c]
        for element in dia[block]:
            if element in rest:
                if "conflicts" in ppl[uid]:
                    ppl[uid]["conflicts"].append("Dia "+str(n)+": "+block+"->"+element)
                else:
                    ppl[uid]["conflicts"] = ["Dia "+str(n)+": "+block+"->"+element]
        blocks.pop(c) #Remove block from list to avoid double notification

def check_conflicts(ppl):
    for uid, values in ppl.items():
        blocksdia1 = re.findall(".(?<!\<)(?=\>)", values["Deseo inscribirme a (día 1):"])
        blocksdia2 = re.findall(".(?<!\<)(?=\>)", values["Deseo inscribirme a (día 2):"])
        blocksdia3 = re.findall(".(?<!\<)(?=\>)", values["Deseo inscribirme a (día 3):"])
        __check_conflicts(blocksdia1, dia1, ppl, uid, 1)
        __check_conflicts(blocksdia2, dia2, ppl, uid, 2)
        __check_conflicts(blocksdia3, dia3, ppl, uid, 3)
        
        if "conflicts" in ppl[uid]:
            print (ppl[uid]["Nombre/s"], "tiene conflictos con tutoriales/workshops de estos bloques:")
            print (ppl[uid]["conflicts"])

def has_conflicts(person):
    if "conflicts" in person:
        return True
    else:
        return False

def get_conflict_body(person):
    msgPlain = "Hola Plain wachi {},\nQué onda vo? Tomá tu dni {}\nTenés conflictos por acá:\n{}".format(person['Nombre/s'], person['DNI'], person['conflicts'])
    msgHtml = "Hola Html wachi {},<br/>Qué onda vo? Tomá tu dni {}<br/>Tenés conflictos por acá:<br/>{}".format(person['Nombre/s'], person['DNI'], person['conflicts'])

    return msgPlain, msgHtml

def get_confirmation_body(person):
    msgPlain = "Hola Plain wachi {},\nQué onda vo? Tomá tu dni {}\nTodo bien por acá\n".format(person['Nombre/s'], person['DNI'])
    msgHtml = "Hola Html wachi {},<br/>Qué onda vo? Tomá tu dni {}<br/>Todo bien por acá:<br/>".format(person['Nombre/s'], person['DNI'])

    return msgPlain, msgHtml

def compose_mail(ppl, start=0):
    max_limit = 400
    if start == len(ppl):
        print("Every email has already been sent")
        return 0

    if start+400 > len(ppl):
       max_limit = len(ppl)-start-1
    for uid, values in itertools.islice(sorted(ppl.items()), start, start+max_limit):
        to = values["Dirección de correo electrónico"]
        subject = 'Inscripción SASE 2019 - Gafete'
        fls = [values['badge'], values['badge-m-cropped']]

        if has_conflicts(ppl[uid]):
            msgPlain, msgHtml = get_conflict_body(ppl[uid])
        else:
            msgPlain, msgHtml = get_confirmation_body(ppl[uid])

        print(msgPlain)
        print(msgHtml)

# DESCOMENTAR ACÁ PARA MANDAR LOS MAILS!
#        result = sendemail.SendMessage(to, subject, msgHtml, msgPlain, creds, fls)    
#        print ("Email sent: ",result)

    return max_limit

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials-sase.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    keys = values[0]
#    print ("KEYS: ", keys)
    del values[0]

# Make a function for formatting - Dict of lists
# Errors in forthcoming functions will be appended to ppl['Errors'].append('Error String'). Generate output log
    ppl = get_formatted_ppl(keys, values)

# Generate QRs
#    generate_qrs(ppl)

# Generate Badges
#    generate_badges(ppl)
    
#    print (ppl["36538926"])

# Crop badges 16:9 for phone
#    crop_badges(ppl)

    print(len(ppl))
    input("Gonna check conflicts. Press Enter to continue...")



# Check that there's no conflicts in tutorials and/or workshops
    count = check_conflicts(ppl)

# Send emails.
# Dummy email, uncomment for testing
#    to = ppl['36538926']['Dirección de correo electrónico']

#    to = "hernangonzalez.234@gmail.com"
#    subject = 'Inscripción SASE 2019 - Gafete'
#    fls = [ppl['36538926']['badge'], ppl['36538926']['badge-m-cropped']]
#    msgPlain = "Hola Plain wachi {},\nQué onda vo? Tomá tu dni {}".format(ppl['36538926']['Nombre/s'], ppl['36538926']['DNI'])
#    msgHtml = "Hola Html wachi {},<br/>Qué onda vo? Tomá tu dni {}".format(ppl['36538926']['Nombre/s'], ppl['36538926']['DNI'])

#    result = sendemail.SendMessage(to, subject, msgHtml, msgPlain, creds, fls)
#    print ("Email sent: ",result)

    try:
        with open('index.txt', 'r+') as lastindex:
            if os.stat("index.txt").st_size == 0:
                start = 0
            else:
                content = int(lastindex.read())
                if content == 0:
                    start = 0
                else:
                    start = content + 1
    except:
        start = 0

    print(start)
    input("Gonna send emails. Press Enter to continue...")
    count = compose_mail(ppl, start)
    start = start + count
    print(start)
    try:
        with open('index.txt', 'w') as lastindex:
            lastindex.write(str(start))
    except:
        print("Couldn't write last index")


if __name__ == '__main__':
    main()
