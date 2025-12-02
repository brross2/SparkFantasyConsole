bios_source = """
-- ==========================================
-- SPARK BIOS - TEXT EDITION
-- ==========================================

t = 0
done = 0
r_x = 10
r_y = 10 
r_w = 140 
r_h = 70
r_cx = 80
r_cy = 80
perim_t = 0

function abs(v) if v < 0 then return -v end return v end

function line(x0, y0, x1, y1, c)
    dx = x1 - x0
    dy = y1 - y0
    steps = 0
    adx = abs(dx)
    ady = abs(dy)
    if adx > ady then 
        steps = adx 
    else 
        steps = ady end
    xinc = 0
    yinc = 0
    if steps > 0 then 
        xinc = dx/steps
        yinc = dy/steps 
    end
    i = 0
    cx=x0
    cy=y0
    
    while i < steps do
        pset(cx, cy, c)
        cx = cx + xinc
        cy = cy + yinc
        i = i + 1
    end
end

function rect(rx, ry, w, h, c)
    j = 0
    while j < h do
        k = 0
        while k < w do pset(rx+k, ry+j, c) k = k+1 end
        j = j+1
    end
end

function update()
    t = t + 1
    if phase == 0 then
        perim_t = perim_t + 3 
        if perim_t > 300 then phase = 1 end
    end
end

function draw()
    -- FASE 0: RAINBOW (Igual que antes)
    if phase == 0 then
        step_draw = 0
        while step_draw < 5 do
            curr_p = perim_t + step_draw
            tx = r_cx
            ty = r_cy
            if curr_p < 70 then
                tx = r_x
                ty = (r_y + r_h) - curr_p
            else
                p2 = curr_p - 70
                if p2 < 140 then 
                    tx = r_x + p2
                    ty = r_y
                else
                    p3 = p2 - 140
                    if p3 < 70 then
                        tx = r_x + r_w
                        ty = r_y + p3
                    else 
                        tx = r_x + r_w
                        ty = r_y + r_h 
                        end
                end
            end
            col = (curr_p / 4) % 32
            line(r_cx, r_cy, tx, ty, col)
            step_draw = step_draw + 1
        end
        -- Cleanup Mask
        rect(r_x, r_cy, r_w+5, 5, 0)
        rect(0, 0, r_x, 160, 0)
        rect(r_x+r_w+1, 0, 20, 160, 0)
        rect(0, 0, 160, r_y, 0)
    end

    -- FASE 1: TEXTO MIXTO
    if phase == 1 then
        
        col = 7 
        if (t % 20) > 10 then col = 6 end
        
        -- Titulo GRANDE (Size 0 o omitido)
        print("SPARK SYSTEM", 26, 95, col)
        
        -- Subtitulos PEQUEÑOS (Size 1)
        -- Nota el ajuste de coordenadas, ahora caben mas cosas
        print("VER 1.0", 65, 110, 13, 1)    -- <--- El 1 al final activa la fuente mini
        print("2025 CORP", 62, 120, 5, 1)   
        
        -- Linea decorativa
        rect(10, 85, 140, 2, 1) 
    end
end
"""