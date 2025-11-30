## Spark Fantasy Console — Especificación Técnica

### 1. Objetivo General

Spark es una fantasy console diseñada para simular hardware retro con limitaciones reales de CPU, memoria y tamaño de cartucho. Permite crear juegos usando un lenguaje sencillo diseñado exclusivamente para la consola.

### 2. Hardware Virtual

* **Resolución:** 160x160 px
* **Paleta:** 32 colores fijos
* **Spritesheet:** 256 sprites de 8x8
* **Mapa:** 128x128 tiles
* **Audio:** 4 canales (pulse, triangle, noise, sample)
* **RAM:** 64 KB de memoria general
* **VRAM:** 16 KB
* **Stack:** 2 KB máximo
* **Cartucho:** 32 KB máximo (bytecode + assets)

### 3. CPU Virtual

* **Velocidad:** 60 ciclos por frame
* **Máximo por segundo:** 3600 ciclos
* **Instrucciones:** pila, aritmética, saltos, llamadas
* **Bytecode:** 1 byte por operación + operandos

### 4. Sistema de Archivos

* Los cartuchos se guardan como `.sparkcart`
* Contienen:

  * Código compilado a bytecode
  * Sprites
  * Mapas
  * Datos de sonido
  * Metadatos

### 5. APIs del Sistema

* `draw()` → llamado cada frame
* `update()` → lógica de juego
* `pset(x, y, c)` → coloca pixel
* `spr(id, x, y)` → dibuja sprite
* `map(x, y)` → dibuja tilemap
* `sfx(id)` → reproduce sonido

---