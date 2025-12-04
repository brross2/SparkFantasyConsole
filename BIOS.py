BIOS_SOURCE = """
function update()

end

function draw()
    -- Variable para el color (0 a 31)
    c = 0
    
    while c < 32 do
        -- Calculamos la posición Y inicial para este color
        -- 160px / 32 colores = 5px de alto por franja
        base_y = c * 5
        
        -- Bucle para el grosor de la línea (5 pixeles de alto)
        off_y = 0
        while off_y < 5 do
            
            -- Bucle para recorrer el ancho de la pantalla (160 pixeles)
            x = 0
            while x < 160 do
                -- Dibujamos el pixel actual
                -- pset(x, y, color)
                pset(x, base_y + off_y, c)
                
                x = x + 1
            end
            
            off_y = off_y + 1
        end
        
        c = c + 1
    end
end
"""