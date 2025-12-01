bios_source = """
-- ==========================================
-- SPARK BIOS - PRISM S EDITION
-- ==========================================

-- CONFIGURACION
t = 0
phase = 0 
perim_t = 0

-- Definicion del Rectangulo del Arcoiris
-- Dejamos margen superior (10) y laterales
r_x = 10
r_y = 10
r_w = 140
r_h = 70
r_cx = 80 -- Centro X (r_x + r_w/2)
r_cy = 80 -- Centro Y (r_y + r_h) -> El origen es ABAJO en el centro

-- ==========================================
-- MATH & GFX
-- ==========================================

function abs(v)
    if v < 0 then return -v end
    return v
end

function line(x0, y0, x1, y1, c)
    dx = x1 - x0
    dy = y1 - y0
    steps = 0
    adx = abs(dx)
    ady = abs(dy)
    if adx > ady then steps = adx else steps = ady end

    xinc = 0
    yinc = 0
    if steps > 0 then
        xinc = dx / steps
        yinc = dy / steps
    end

    i = 0
    cur_x = x0
    cur_y = y0
    while i < steps do
        pset(cur_x, cur_y, c)
        cur_x = cur_x + xinc
        cur_y = cur_y + yinc
        i = i + 1
    end
    pset(x1, y1, c)
end

function rect(rx, ry, w, h, c)
    j = 0
    while j < h do
        k = 0
        while k < w do
            pset(rx + k, ry + j, c)
            k = k + 1
        end
        j = j + 1
    end
end

-- ==========================================
-- PIXEL ART LOGO "S"
-- ==========================================
-- Dibuja una S estilizada de 32x40 pixels
function draw_big_s(cx, cy, c)
    -- Grosor de trazo
    th = 6
    w = 20 -- mitad ancho

    -- 1. TOP
    -- Barra horizontal superior (con esquinas recortadas)
    rect(cx - w + th, cy - 20, w*2 - th*2, th, c)
    -- Vertical Izquierda Arriba
    rect(cx - w, cy - 20 + th, th, 10, c)
    -- Punta decorativa derecha arriba
    rect(cx + w - th, cy - 20 + th, th, 4, c)

    -- 2. MID
    -- Barra central
    rect(cx - w + th, cy - 3, w*2 - th*2, th, c)

    -- 3. BOT
    -- Vertical Derecha Abajo
    rect(cx + w - th, cy - 3 + th, th, 10, c)
    -- Barra inferior
    rect(cx - w + th, cy + 14, w*2 - th*2, th, c)
    -- Punta decorativa izquierda abajo
    rect(cx - w, cy + 10, th, 4, c)
end

-- ==========================================
-- MAIN LOOPS
-- ==========================================

function update()
    t = t + 1

    -- Fase 0: Rainbow Sweep
    -- Recorremos el perimetro de izquierda a derecha (arco de 180 grados aprox)
    if phase == 0 then
        -- Velocidad de llenado
        perim_t = perim_t + 3

        -- El perimetro de un arco superior es: Izquierda -> Arriba -> Derecha
        -- Altura 70 (x2 lados) + Ancho 140 = 280 steps aprox
        if perim_t > 300 then
            phase = 1
        end
    end
end

function draw()
    -- FASE 0: RAINBOW GENERATION
    if phase == 0 then
        -- Dibujamos varias lineas por frame para rellenar huecos (densidad)
        step_draw = 0
        while step_draw < 5 do
            curr_p = perim_t + step_draw

            -- Calculamos destino en el borde del rectangulo
            tx = r_cx
            ty = r_cy

            -- Logica de recorrido (U invertida)
            -- 1. Subiendo por la izquierda (70 pixels)
            if curr_p < 70 then
                tx = r_x
                ty = (r_y + r_h) - curr_p
            else
                -- 2. Recorriendo el techo (140 pixels)
                p2 = curr_p - 70
                if p2 < 140 then
                    tx = r_x + p2
                    ty = r_y
                else
                    -- 3. Bajando por la derecha (70 pixels)
                    p3 = p2 - 140
                    if p3 < 70 then
                        tx = r_x + r_w
                        ty = r_y + p3
                    else
                        -- Fin del recorrido, mantenemos ultimo punto
                        tx = r_x + r_w
                        ty = r_y + r_h
                    end
                end
            end

            -- Color ciclico (Velocidad del cambio de color)
            col_idx = (curr_p / 4) % 32

            -- Dibujar linea desde el CENTRO INFERIOR hacia el borde
            line(r_cx, r_cy, tx, ty, col_idx)

            step_draw = step_draw + 1
        end

        -- CLEANUP (MASCARA DE RECORTE)
        -- Dibujamos cajas negras alrededor para ocultar las lineas que se salen
        -- 1. Tapa Inferior (corta el centro del abanico para dejarlo plano)
        rect(r_x, r_cy, r_w + 5, 5, 0)

        -- 2. Tapa Izquierda
        rect(0, 0, r_x, 160, 0)

        -- 3. Tapa Derecha
        rect(r_x + r_w + 1, 0, 20, 160, 0)

        -- 4. Tapa Superior
        rect(0, 0, 160, r_y, 0)
    end

    -- FASE 1: THE S LOGO
    if phase == 1 then
        -- Dibujamos la S en el centro de la parte inferior
        -- Usamos color blanco (7) con un pequeño parpadeo al final
        c_logo = 7

        -- Animacion de entrada (parpadeo rapido)
        if t < 120 then
            if (t % 10) > 5 then c_logo = 6 end -- Gris
        else
            c_logo = 7 -- Blanco solido
        end

        -- Posicion Y: Debajo del arcoiris (r_y + r_h + margen)
        draw_big_s(80, 120, c_logo)
    end
end
"""