# -*- coding: utf-8 -*-
# runtime.py - Version corregida para Python 2.7 con Tkinter y Menú Integrado

import sys
import json
import time
import random
import Tkinter as tk
import tkMessageBox as messagebox

CONFIG_DIFICULTADES = {
    "facil": {
        "permitir_veneno": False,
        "permitir_obstaculos": False,
        "permitir_powerup": False,
        "probabilidad_veneno_por_comida": 0.0,
        "velocidad": 0.16                 
    },
    "normal": {
        "permitir_veneno": True,
        "permitir_obstaculos": True,
        "permitir_powerup": True,
        "probabilidad_veneno_por_comida": 0.3,
        "velocidad": 0.15                  
    },
    "nyan cat": {
        "permitir_veneno": True,
        "permitir_obstaculos": True,
        "permitir_powerup": False,
        "probabilidad_veneno_por_comida": 0.6,
        "velocidad": 0.08                  
    }
}

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.grid_color = [[None for _ in range(self.ancho)] for _ in range(self.alto)]
        self.shapes = self.datos_juego.get('shapes', {})
        self.puntuacion = 0
        self.juego_terminado = False
        self.forzar_bloque_1x1 = False
        
        self.dificultad = "facil"
        
        # Configuracion
        config_speed = config.get('speed', 0.4)
        self.speed_multiplier = config.get('speed', 1.0)
        self.snake_shape = config.get('snake_shape', 'SQUARE')
        
        # Variables de juego vacías al inicio
        self.pieza_actual = None
        self.nombre_pieza_actual = None
        self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
        self.velocidad_gravedad = 0.4
        
        self.serpiente_cuerpo = []
        self.serpiente_direccion = (1, 0)
        self.posicion_comida = None
        self.creciendo = 0
        self.posiciones_veneno = []
        self.posiciones_obstaculos = []
        self.posicion_powerup = None
        self.invencible_activo = False
        self.invencible_hasta = 0
        
        self.timer_gravedad = 0
        self.timer_id = None
        
        # GUI Principal
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        if self.tipo_juego == 'SNAKE':
            self.mostrar_menu_dificultad()
        else:
            self.comenzar_con_dificultad("normal")

    def mostrar_menu_dificultad(self):
        # Contenedor del menú para poder destruirlo fácilmente después
        self.marco_menu = tk.Frame(self.root, bg='#222222', padx=50, pady=40)
        self.marco_menu.pack(fill=tk.BOTH, expand=True)
        
        lbl_titulo = tk.Label(self.marco_menu, text="SELECCIONA DIFICULTAD", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        lbl_titulo.pack(pady=15)
        
        # Botones para cada dificultad
        btn_facil = tk.Button(self.marco_menu, text="FÁCIL", font=('Consolas', 12, 'bold'), bg='#4CAF50', fg='white', width=15, command=lambda: self.comenzar_con_dificultad("facil"))
        btn_facil.pack(pady=8)
        
        btn_normal = tk.Button(self.marco_menu, text="NORMAL", font=('Consolas', 12, 'bold'), bg='#FF9800', fg='white', width=15, command=lambda: self.comenzar_con_dificultad("normal"))
        btn_normal.pack(pady=8)
        
        btn_nyan = tk.Button(self.marco_menu, text="NYAN CAT", font=('Consolas', 12, 'bold'), bg='#00E5FF', fg='black', width=15, command=lambda: self.comenzar_con_dificultad("nyan cat"))
        btn_nyan.pack(pady=8)

    def comenzar_con_dificultad(self, dificultad_elegida):
        self.dificultad = dificultad_elegida
        
        if hasattr(self, 'marco_menu') and self.marco_menu:
            self.marco_menu.destroy()
        
        # Construimos la interfaz del juego real
        self.taman_celda = 25
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)
        
        # Pequeño indicador de dificultad en la barra lateral
        self.label_dif = tk.Label(self.marco_score, text="MODO: " + self.dificultad.upper(), bg='#222222', fg='#FFD700', font=('Consolas', 9, 'bold'))
        self.label_dif.pack(pady=5)
        
        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)
        
        self.root.bind('<Key>', self.manejar_input_gui)
        
        # Ajustes de velocidad inicial según el juego
        config_actual = CONFIG_DIFICULTADES.get(self.dificultad, {})
        
        velocidad_por_defecto = 0.15 if self.tipo_juego == 'SNAKE' else 0.4
        self.velocidad_gravedad = config_actual.get('velocidad', velocidad_por_defecto)
            
        self.ejecutar_evento('ON_START')
        self.run()

    def run(self):
        self.root.after(50, self.game_loop)

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        if self.tipo_juego == 'SNAKE' and self.invencible_activo:
            if time.time() > self.invencible_hasta:
                self.invencible_activo = False

        self.timer_gravedad += 0.05
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')

        self.dibujar()
        self.timer_id = self.root.after(50, self.game_loop)

    def dibujar(self):
        self.canvas.delete("all")
        
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] > 0:
                    color = self.grid_color[y][x] if self.grid_color[y][x] else '#CCCCCC'
                    self.dibujar_celda(x, y, color)
        
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            color_pieza = self.shapes.get(self.nombre_pieza_actual, {}).get('color', '#00FFFF')
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, color_pieza)
        
        if self.tipo_juego == 'SNAKE':
            for obs in self.posiciones_obstaculos:
                self.dibujar_celda(obs[0], obs[1], '#666666', shape='SQUARE')
                
            for veneno in self.posiciones_veneno:
                self.dibujar_celda(veneno[0], veneno[1], '#800080', shape='CIRCULAR')
                
            if self.posicion_powerup:
                self.dibujar_celda(self.posicion_powerup[0], self.posicion_powerup[1], '#FFD700', shape='TRIANGULAR')

            if self.posicion_comida:
                x, y = self.posicion_comida
                self.dibujar_celda(x, y, '#FF0000', shape='SQUARE')
                
            colores_arcoiris = ['#FF0000', '#FF9900', '#FFFF00', '#33CC33', '#0099FF', '#6633FF']
            
            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                ts = self.taman_celda
                x1, y1 = x * ts, y * ts
                x2, y2 = x1 + ts, y1 + ts
                
                if i == 0:  # 🐱 ¿Es la cabeza?
                    if self.dificultad == "nyan cat":
                        color_gato = '#ACA8A1'
                        color_texto = '#000000'
                        
                        self.canvas.create_oval(x1, y1, x2, y2, fill=color_gato, outline='#000000')
                        
                        # Orejitas
                        self.canvas.create_polygon(x1 + (ts*0.05), y1 + (ts*0.1), x1 + (ts*0.35), y1 + (ts*0.05), x1 + (ts*0.15), y1 - (ts*0.22), fill=color_gato, outline='#000000')
                        self.canvas.create_polygon(x2 - (ts*0.35), y1 + (ts*0.05), x2 - (ts*0.05), y1 + (ts*0.1), x2 - (ts*0.15), y1 - (ts*0.22), fill=color_gato, outline='#000000')
                        
                        # Rostro (:ω)
                        centro_x = (x1 + x2) / 2.0
                        centro_y = (y1 + y2) / 2.0
                        self.canvas.create_text(centro_x, centro_y, text=":\xcf\x89", fill=color_texto, font=('Consolas', int(ts*0.48), 'bold'))
                    else:
                        # Cabeza normal en Fácil/Normal (Blanca si es invencible, Verde si no)
                        color = '#FFFFFF' if self.invencible_activo else '#00FF00'
                        self.dibujar_celda(x, y, color, shape=self.snake_shape)
                        
                else: 
                    if self.dificultad == "nyan cat":
                        color_ciclo = colores_arcoiris[(i - 1) % len(colores_arcoiris)]
                        self.dibujar_celda(x, y, color_ciclo, shape='SQUARE')
                    else:
                        color = '#FFFFFF' if self.invencible_activo else '#33CC33'
                        self.dibujar_celda(x, y, color, shape=self.snake_shape)
        
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))

    def dibujar_celda(self, x, y, color, shape='SQUARE'):
        ts = self.taman_celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        
        if shape == 'CIRCULAR':
            self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline='#000000')
        elif shape == 'TRIANGULAR':
            mitad_x = (x1 + x2) / 2.0
            self.canvas.create_polygon(mitad_x, y1, x1, y2, x2, y2, fill=color, outline='#000000')
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def ejecutar_evento(self, nombre_evento):
        if nombre_evento not in self.datos_juego.get('events', {}):
            return
        
        for accion in self.datos_juego['events'][nombre_evento]:
            verbo = accion.get('accion')
            objeto = accion.get('objeto')
            params = accion.get('params', [])
            
            if verbo == 'INCREASE_SCORE':
                self.puntuacion += int(objeto)
            elif verbo == 'DECREASE_SCORE':
                self.puntuacion -= int(objeto)
                if self.puntuacion <= 0:
                    self.puntuacion = 0
                    self.juego_terminado = True
            elif verbo == 'LOSE_ALL_SCORE':
                self.puntuacion = 0
                self.juego_terminado = True
            elif verbo == 'GAME_OVER':
                self.juego_terminado = True
            elif verbo == 'MAKE_INVINCIBLE':
                self.invencible_hasta = time.time() + int(objeto)
                self.invencible_activo = True
            elif verbo == 'GROW':
                self.creciendo += int(params[0]) if params else 1
            
            if self.tipo_juego == 'TETRIS':
                if verbo == 'SPAWN':
                    if objeto == 'PIECE' or objeto == 'RANDOM_SHAPE':
                        self.tetris_spawn_pieza()
                    elif objeto in self.shapes:
                        self.tetris_spawn_pieza(objeto)
                elif verbo == 'MOVE':
                    if params:
                        self.tetris_mover_pieza(params[0])
                elif verbo == 'ROTATE':
                    self.tetris_rotar_pieza()
            
            elif self.tipo_juego == 'SNAKE':
                if verbo == 'SPAWN':
                    if objeto == 'PLAYER':
                        self.snake_spawn_jugador(params)
                    elif objeto in ['FOOD', 'POISON', 'OBSTACLE', 'POWERUP_INVINCIBLE']:
                        self.snake_spawn_element(objeto)
                elif verbo == 'MOVE' and objeto == 'PLAYER':
                    self.snake_mover_jugador()

    # --- Funciones Tetris Omitidas del todo para ahorrar espacio y mantenerlas identicas ---
    def tetris_spawn_pieza(self, nombre_pieza=None):
        if self.forzar_bloque_1x1:
            self.nombre_pieza_actual = 'BLOQUE_BONUS'
            self.pieza_actual = [[[1]]]
            self.pieza_x = self.ancho / 2 - 1
            self.pieza_y = 0
            self.pieza_rotacion = 0
            self.forzar_bloque_1x1 = False
            if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, 0): self.juego_terminado = True
            return
        if nombre_pieza is None: nombre_pieza = self.tetris_elegir_pieza()
        self.nombre_pieza_actual = nombre_pieza
        self.pieza_actual = self.shapes[nombre_pieza]['estados']
        self.pieza_x = self.ancho / 2 - 2
        self.pieza_y = 0
        self.pieza_rotacion = 0
        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, 0): self.juego_terminado = True

    def tetris_elegir_pieza(self):
        opciones = []
        total = 0
        for nombre, info in self.shapes.items():
            chance = int(info.get('chance', 1))
            if chance > 0:
                opciones.append((nombre, chance))
                total += chance
        if total <= 0 or not opciones: return self.shapes.keys()[0]
        objetivo = random.uniform(0, total)
        acumulado = 0
        for nombre, chance in opciones:
            acumulado += chance
            if objetivo <= acumulado: return nombre
        return opciones[-1][0] if opciones else self.shapes.keys()[0]

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual: return
        dx, dy = 0, 0
        if direccion == 'LEFT': dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN': dy = 1
        if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion
    
    def tetris_fijar_pieza(self):
        if not self.pieza_actual: return
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        if self.nombre_pieza_actual == 'BLOQUE_BONUS': color_actual = '#FFFFFF'
        else: color_actual = self.shapes[self.nombre_pieza_actual].get('color', '#00FFFF')
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    y_pos = int(self.pieza_y + y_offset)
                    x_pos = int(self.pieza_x + x_offset)
                    if 0 <= y_pos < self.alto and 0 <= x_pos < self.ancho:
                        self.grid[y_pos][x_pos] = 1
                        self.grid_color[y_pos][x_pos] = color_actual
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.tetris_spawn_pieza()
    
    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        x, y = int(x), int(y)
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto): return True
                    if nuevo_y >= 0 and self.grid[nuevo_y][nuevo_x] > 0: return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid, nuevo_color = [], []
        for y in range(self.alto):
            if sum(self.grid[y]) < self.ancho:
                nuevo_grid.append(list(self.grid[y]))
                nuevo_color.append(list(self.grid_color[y]))
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            self.grid_color = [[None] * self.ancho for _ in range(lineas_limpias)] + nuevo_color
            for _ in range(lineas_limpias): self.ejecutar_evento('ON_LINE_CLEAR')
            if lineas_limpias >= 3:
                self.ejecutar_evento('ON_TRIPLE_LINE_CLEAR')
                self.forzar_bloque_1x1 = True

    # --- Funciones Extendidas Snake ---
    def snake_spawn_jugador(self, params):
        coords = params[0] if params else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo = [(int(coords[0]), int(coords[1]))]
        self.serpiente_direccion = (1, 0)

    def obtener_posicion_libre(self):
        ocupadas = set(self.serpiente_cuerpo)
        if self.posicion_comida: ocupadas.add(self.posicion_comida)
        if self.posicion_powerup: ocupadas.add(self.posicion_powerup)
        ocupadas.update(self.posiciones_veneno)
        ocupadas.update(self.posiciones_obstaculos)
        
        libres = [(x, y) for x in range(self.ancho) for y in range(self.alto) if (x, y) not in ocupadas]
        if libres:
            return random.choice(libres)
        return None

    def snake_spawn_element(self, tipo):
        pos = self.obtener_posicion_libre()
        if not pos: return
        
        config_actual = CONFIG_DIFICULTADES.get(self.dificultad, {})
        
        if tipo == 'FOOD':
            self.posicion_comida = pos
        elif tipo == 'POISON' and config_actual.get('permitir_veneno', True):
            self.posiciones_veneno.append(pos)
        elif tipo == 'OBSTACLE' and config_actual.get('permitir_obstaculos', True):
            self.posiciones_obstaculos.append(pos)
        elif tipo == 'POWERUP_INVINCIBLE' and config_actual.get('permitir_powerup', True):
            self.posicion_powerup = pos

    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)
        
        # 🔑 DETECTAR COLISIONES
        colision_detectada = False
        tipo_colision = None
        
        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
            colision_detectada = True
            tipo_colision = 'ON_COLLISION_WALL'
            
        elif nueva_cabeza in self.serpiente_cuerpo[:-1]:
            colision_detectada = True
            tipo_colision = 'ON_COLLISION_SELF'
            
        elif nueva_cabeza in self.posiciones_obstaculos:
            colision_detectada = True
            tipo_colision = 'ON_COLLISION_OBSTACLE'

        if colision_detectada and self.dificultad == "nyan cat":
            if self.invencible_activo:
                return 
                
            if self.puntuacion > 0:
                self.puntuacion = 0
                self.invencible_hasta = time.time() + 1.5
                self.invencible_activo = True
                return  
            else:
                self.juego_terminado = True
                return
            
        if colision_detectada:
            if self.invencible_activo: return
            self.ejecutar_evento(tipo_colision)
            return

        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        
        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD')
            
            config_actual = CONFIG_DIFICULTADES.get(self.dificultad, {})
            prob_veneno = config_actual.get('probabilidad_veneno_por_comida', 0.4)
            
            if random.random() < prob_veneno: 
                self.snake_spawn_element('POISON')
                
            if not self.posicion_powerup and random.random() < 0.2:
                self.snake_spawn_element('POWERUP_INVINCIBLE')
                
        elif nueva_cabeza in self.posiciones_veneno:
            self.posiciones_veneno.remove(nueva_cabeza)
            if not self.invencible_activo:
                self.ejecutar_evento('ON_EAT_POISON')
                
        elif nueva_cabeza == self.posicion_powerup:
            self.posicion_powerup = None
            self.ejecutar_evento('ON_EAT_INVINCIBLE')
        
        if self.creciendo > 0:
            self.creciendo -= 1
        else:
            self.serpiente_cuerpo.pop()

    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        
        elif self.tipo_juego == 'SNAKE':
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def cerrar_ventana(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def mostrar_game_over(self):
        messagebox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.cerrar_ventana()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python runtime.py <archivo_juego.json>")
        sys.exit(1)
    
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except IOError:
        print("Error: No se pudo encontrar el archivo " + archivo_juego)
        sys.exit(1)
    
    juego = Juego(datos_juego)
    juego.root.mainloop() # Movemos el mainloop al script principal para soportar el menú previo