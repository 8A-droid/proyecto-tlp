# compiler.py
# Compilador universal para BrickScript (Version Final y Depurada)
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import re
import json

def lexer(codigo_fuente):
    # Remove comments, but preserve hex color values like #FF00AA
    codigo_fuente = re.sub(r'#(?![A-Fa-f0-9]{6}\b).*', '', codigo_fuente)
    token_regex = r'\b[A-Z_]+\b|#[A-Fa-f0-9]{6}|\d+|[\[\](),:]'
    tokens = re.findall(token_regex, codigo_fuente)
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.ast = {"tipo_juego": None, "config": {}, "shapes": {}, "powerups": {}, "events": {}}

    def parse(self):
        while self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion]
            if token_actual == 'GAME_TYPE':
                self.parsear_tipo_juego()
            elif token_actual == 'GAME_GRID':
                self.parsear_grid()
            elif token_actual == 'DEFINE':
                if self.posicion + 1 < len(self.tokens) and self.tokens[self.posicion + 1] == 'SHAPE':
                    self.parsear_shape()
                elif self.posicion + 1 < len(self.tokens) and self.tokens[self.posicion + 1] == 'POWERUP':
                    self.parsear_powerup()
                else:
                    self.posicion += 1
            elif token_actual == 'SNAKE_SHAPE':
                self.consumir('SNAKE_SHAPE')
                self.ast['config']['snake_shape'] = self.consumir()
            elif token_actual == 'ON':
                self.parsear_evento()
            else:
                self.posicion += 1
        return self.ast

    def consumir(self, token_esperado=None):
        if self.posicion < len(self.tokens):
            token = self.tokens[self.posicion]
            if token_esperado and token != token_esperado:
                raise Exception("Error de sintaxis: Se esperaba '" + token_esperado + "' pero se encontro '" + token + "'")
            self.posicion += 1
            return token
        if token_esperado:
            raise Exception("Error de sintaxis: Se esperaba '" + token_esperado + "' pero se llego al final del archivo.")
        return None

    def parsear_tipo_juego(self):
        self.consumir('GAME_TYPE')
        self.ast['tipo_juego'] = self.consumir()

    def parsear_grid(self):
        self.consumir('GAME_GRID')
        self.consumir('(')
        ancho = int(self.consumir())
        self.consumir(',')
        alto = int(self.consumir())
        self.consumir(')')
        self.ast['config']['grid_size'] = [ancho, alto]
        # Valores por defecto para retrocompatibilidad
        if 'speed' not in self.ast['config']:
            self.ast['config']['speed'] = 0.4 if self.ast['tipo_juego'] == 'TETRIS' else 0.15
        if 'color_grid_fija' not in self.ast['config']:
            self.ast['config']['color_grid_fija'] = '#343434'
        if 'snake_shape' not in self.ast['config']:
            self.ast['config']['snake_shape'] = 'SQUARE'

    def parsear_shape(self):
        self.consumir('DEFINE')
        self.consumir('SHAPE')
        nombre_shape = self.consumir()
        self.consumir(':')
        
        color = "#00FFFF"
        chance = 1
        estados = []
        
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            t = self.tokens[self.posicion]
            
            if t == 'COLOR':
                self.consumir('COLOR')
                self.consumir(':')
                
                # Leemos el codigo de color
                token_color = self.consumir()
                if token_color and token_color.startswith('#'):
                    color = token_color
                else:
                    color = token_color
                    
            elif t == 'CHANCE':
                self.consumir('CHANCE')
                self.consumir(':')
                chance = int(self.consumir())
                
            elif t == 'STATE':
                self.consumir('STATE')
                self.consumir() # Salta el numero de estado
                self.consumir(':')
                matriz = []
                while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                    fila = []
                    self.consumir('[')
                    while self.tokens[self.posicion] != ']':
                        val = self.consumir()
                        if val != ',': fila.append(int(val))
                    self.consumir(']')
                    matriz.append(fila)
                estados.append(matriz)
            else:
                self.posicion += 1

        self.consumir('END')
        # Guardamos la estructura que el Runtime espera
        self.ast['shapes'][nombre_shape] = {'estados': estados, 'color': color, 'chance': chance}

    def parsear_powerup(self):
        self.consumir('DEFINE')
        self.consumir('POWERUP')
        nombre_powerup = self.consumir()
        self.consumir(':')

        color = "#FFFFFF"
        chance = 1
        estados = []

        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            t = self.tokens[self.posicion]

            if t == 'COLOR':
                self.consumir('COLOR')
                self.consumir(':')
                token_color = self.consumir()
                if token_color and token_color.startswith('#'):
                    color = token_color
                else:
                    color = token_color

            elif t == 'CHANCE':
                self.consumir('CHANCE')
                self.consumir(':')
                chance = int(self.consumir())

            elif t == 'STATE':
                self.consumir('STATE')
                self.consumir() # Salta el numero de estado
                self.consumir(':')
                matriz = []
                while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                    fila = []
                    self.consumir('[')
                    while self.tokens[self.posicion] != ']':
                        val = self.consumir()
                        if val != ',': fila.append(int(val))
                    self.consumir(']')
                    matriz.append(fila)
                estados.append(matriz)
            else:
                self.posicion += 1

        self.consumir('END')
        self.ast['powerups'][nombre_powerup] = {'estados': estados, 'color': color, 'chance': chance}

    # --- FUNCION CORREGIDA ---
    def parsear_evento(self):
        self.consumir('ON')
        nombre_evento = 'ON_' + self.consumir()
        self.consumir(':')
        acciones = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion] != 'END':
            verbo = self.consumir()
            
            # Si el comando es de una sola palabra, lo anadimos y continuamos
            if verbo == 'GAME_OVER':
                acciones.append({'accion': verbo, 'objeto': None, 'params': []})
                continue
            
            # Si no, parseamos el resto de la accion
            objeto = self.consumir()
            params = []
            if self.posicion < len(self.tokens) and self.tokens[self.posicion] == 'AT':
                self.consumir('AT')
                if self.tokens[self.posicion] == 'RANDOM':
                    params.append(self.consumir())
                else:
                    self.consumir('(')
                    x = int(self.consumir())
                    self.consumir(',')
                    y = int(self.consumir())
                    self.consumir(')')
                    params.append([x, y])
            elif self.posicion < len(self.tokens) and self.tokens[self.posicion] not in ['END', 'ON', 'DEFINE', 'SPAWN', 'MOVE', 'ROTATE', 'INCREASE_SCORE', 'SET_DIRECTION', 'GROW', 'GAME_OVER']:
                params.append(self.consumir())
            acciones.append({'accion': verbo, 'objeto': objeto, 'params': params})
        self.consumir('END')
        self.ast['events'][nombre_evento] = acciones

def generar_codigo(ast, archivo_salida):
    with open(archivo_salida, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print ("Uso: python compiler.py <archivo_entrada.brick>")
        sys.exit(1)
    archivo_entrada = sys.argv[1]
    archivo_salida = archivo_entrada.replace('.brick', '.json')
    print ("Compilando " + archivo_entrada + "...")
    try:
        with open(archivo_entrada, 'r') as f:
            codigo = f.read()
        tokens = lexer(codigo)
        parser = Parser(tokens)
        ast = parser.parse()
        generar_codigo(ast, archivo_salida)
        print ("Compilacion exitosa! Archivo de juego creado en " + archivo_salida)
    except Exception as e:
        print ("\n!!! ERROR DE COMPILACION !!!")
        print (str(e))
        sys.exit(1)