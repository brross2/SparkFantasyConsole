# language.md

# SparkLang — Especificación del Lenguaje

SparkLang es un lenguaje pequeño inspirado en Lua y Python. Está diseñado para ser fácil de aprender y perfecto para un entorno retro.

## 1. Tipos de Datos

* `int`
* `float`
* `bool`
* `string`
* `array`
* `null`

## 2. Variables

```
x = 10
name = "spark"
```

## 3. Funciones

```
function move()
    x = x + 1
end
```

## 4. Condicionales

```
if x < 10:
    x = x + 1
end
```

## 5. Bucles

```
while x < 50:
    x = x + 1
end
```

## 6. Comentarios

```
-- esto es un comentario
```

## 7. Funciones del Sistema

```
pset(x, y, color)
spr(id, x, y)
sfx(id)
```

## 8. Entry Points

```
function update()
    -- lógica por frame
end

function draw()
    -- dibuja cada frame
end
```
