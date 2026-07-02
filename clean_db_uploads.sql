-- Script de Normalización y Limpieza de rutas de archivos en MySQL
-- Este script normaliza las rutas antiguas que contenían "/uploads/" a la nueva estructura "/static/uploads/"
-- o limpia aquellas que no se puedan renderizar directamente.

-- 1. Normalizar la columna 'foto_perfil' en la tabla 'pacientes'
UPDATE pacientes 
SET foto_perfil = REPLACE(REPLACE(foto_perfil, '/uploads/', '/static/uploads/'), 'uploads/', '/static/uploads/')
WHERE foto_perfil LIKE '%uploads/%' AND foto_perfil NOT LIKE '%/static/uploads/%';

-- 2. Limpieza de rutas corruptas (no válidas) en pacientes
-- Si queda alguna ruta que no sea un path /static/uploads/ ni comience con http/https (nube) o base64 (data:), la ponemos a NULL
UPDATE pacientes
SET foto_perfil = NULL
WHERE foto_perfil IS NOT NULL 
  AND foto_perfil NOT LIKE '/static/uploads/%'
  AND foto_perfil NOT LIKE 'http://%'
  AND foto_perfil NOT LIKE 'https://%'
  AND foto_perfil NOT LIKE 'data:%';
