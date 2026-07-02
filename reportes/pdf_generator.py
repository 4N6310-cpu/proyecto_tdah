import os
import io
import base64
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class PDFReportGenerator:
    @staticmethod
    def generar_grafico_timeline(timeline):
        """
        Genera un gráfico de línea de tiempo con Matplotlib en memoria (Agg headless).
        Grafica la atención (área sombreada) y el Fidgeting (línea continua) segundo a segundo.
        Retorna la imagen codificada en Base64.
        """
        if not timeline:
            # Crear un gráfico vacío por si no hay datos
            plt.figure(figsize=(7, 2.5))
            plt.text(0.5, 0.5, "Sin datos de comportamiento", ha='center', va='center')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close()
            buf.seek(0)
            return base64.b64encode(buf.read()).decode('utf-8')

        segundos = [d["segundo"] for d in timeline]
        atencion = [d["atencion"] for d in timeline]
        fidgeting = [d["fidgeting_score"] for d in timeline]
        
        fig, ax1 = plt.subplots(figsize=(7, 2.8))
        
        # Graficar Atención como un área sombreada verde suave/rojo suave
        color_atencion = '#E2F0D9' # Verde suave para atencion
        color_distraccion = '#FCE4D6' # Rojo suave para distraccion
        
        # Graficar fondo según el estado de atención
        # Convertimos a formato de escalón
        for i in range(len(segundos) - 1):
            t_inicio = segundos[i]
            t_fin = segundos[i+1]
            estado = atencion[i]
            c = color_atencion if estado == 1 else color_distraccion
            ax1.axvspan(t_inicio, t_fin, color=c, alpha=0.8, ymin=0, ymax=1.0)
            
        ax1.set_xlabel('Tiempo de Sesión (segundos)', fontsize=9, fontweight='bold', color='#333333')
        ax1.set_ylabel('Foco Visual (Verde=Atento / Rojo=Distraído)', color='#2E5B82', fontsize=9, fontweight='bold')
        ax1.set_yticks([]) # Quitar marcas del eje Y ya que es binario
        ax1.set_xlim(min(segundos), max(segundos))
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # Crear segundo eje Y para el Fidgeting / Hiperactividad
        ax2 = ax1.twinx()
        ax2.plot(segundos, fidgeting, color='#C00000', linewidth=2.0, label='Nivel de Fidgeting')
        ax2.fill_between(segundos, fidgeting, color='#C00000', alpha=0.1)
        ax2.set_ylabel('Score de Fidgeting / Hiperactividad (0 - 10)', color='#C00000', fontsize=9, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='#C00000')
        ax2.set_ylim(0, 10.5)
        
        plt.title('Dinámica Temporal de la Sesión: Atención vs. Hiperactividad', fontsize=11, fontweight='bold', pad=10, color='#1A365D')
        fig.tight_layout()
        
        # Guardar gráfico en un buffer de bytes en memoria
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
        plt.close()
        buf.seek(0)
        
        # Convertir el contenido del buffer a Base64
        imagen_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return imagen_base64

    @classmethod
    def generar_pdf_clinico(cls, paciente, analisis, path_salida):
        """
        Crea un PDF formal, limpio y con una estética médica premium para el terapeuta.
        """
        # Crear documento PDF
        doc = SimpleDocTemplate(
            path_salida,
            pagesize=letter,
            rightMargin=40, leftMargin=40,
            topMargin=40, bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        
        # Definición de la Paleta de Colores
        COLOR_PRIMARIO = colors.HexColor("#1A365D")  # Azul Clínico Oscuro
        COLOR_SECUNDARIO = colors.HexColor("#2B6CB0") # Azul Intermedio
        COLOR_TEXTO = colors.HexColor("#2D3748")      # Gris Oscuro
        COLOR_FONDO_TABLA = colors.HexColor("#F7FAFC")# Blanco grisáceo
        
        # Estilos Personalizados
        style_titulo = ParagraphStyle(
            name='TituloClinico',
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=COLOR_PRIMARIO,
            spaceAfter=15
        )
        
        style_subtitulo = ParagraphStyle(
            name='SubtituloClinico',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=COLOR_SECUNDARIO,
            spaceAfter=10,
            keepWithNext=True
        )
        
        style_cuerpo = ParagraphStyle(
            name='CuerpoClinico',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXTO,
            spaceAfter=8
        )
        
        style_cuerpo_bold = ParagraphStyle(
            name='CuerpoClinicoBold',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXTO,
            spaceAfter=8
        )
        
        style_conclusion = ParagraphStyle(
            name='ConclusionClinica',
            fontName='Helvetica-Oblique',
            fontSize=10.5,
            leading=15,
            textColor=COLOR_PRIMARIO,
            spaceAfter=10
        )
        
        story = []
        
        # ---- ENCABEZADO Y TÍTULO ----
        story.append(Paragraph("INFORME DE COMPORTAMIENTO CLÍNICO (TDAH)", style_titulo))
        story.append(Paragraph(f"<b>ID de Análisis:</b> {analisis['id']} | <b>Fecha de Sesión:</b> {analisis['fecha']}", style_cuerpo))
        story.append(Spacer(1, 10))
        
        # Dibujar una línea divisoria
        t_linea = Table([[""]], colWidths=[doc.width])
        t_linea.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1.5, COLOR_PRIMARIO),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_linea)
        story.append(Spacer(1, 12))
        
        # ---- INFORMACIÓN GENERAL DEL PACIENTE Y SESIÓN ----
        datos_paciente = [
            [
                Paragraph("<b>DATOS DEL PACIENTE</b>", style_subtitulo),
                Paragraph("<b>DATOS DE EVALUACIÓN</b>", style_subtitulo)
            ],
            [
                Paragraph(f"<b>Nombre:</b> {paciente['nombre']}", style_cuerpo),
                Paragraph(f"<b>Terapeuta:</b> {paciente.get('terapeuta_nombre', 'Especialista Asignado')}", style_cuerpo)
            ],
            [
                Paragraph(f"<b>Edad:</b> {paciente['edad']} años", style_cuerpo),
                Paragraph(f"<b>Video Analizado:</b> {analisis['video_origen']}", style_cuerpo)
            ],
            [
                Paragraph(f"<b>Tutor:</b> {paciente['tutor']}", style_cuerpo),
                Paragraph(f"<b>Duración de Análisis:</b> {analisis['duracion_total_seg']} seg", style_cuerpo)
            ]
        ]
        
        t_info = Table(datos_paciente, colWidths=[doc.width/2.0, doc.width/2.0])
        t_info.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 15))
        
        # ---- MÉTRICAS OBJETIVAS (INDICADORES) ----
        story.append(Paragraph("INDICADORES DE ATENCIÓN E HIPERACTIVIDAD OBJETIVOS", style_subtitulo))
        
        # Crear tabla de indicadores
        datos_metricas = [
            [
                Paragraph("<b>Métrica Cuantitativa</b>", style_cuerpo_bold),
                Paragraph("<b>Valor Registrado</b>", style_cuerpo_bold),
                Paragraph("<b>Interpretación Clínica Inicial</b>", style_cuerpo_bold)
            ],
            [
                Paragraph("Porcentaje de Atención Sostenida", style_cuerpo),
                Paragraph(f"<b>{analisis['atencion_porcentaje']}%</b>", style_cuerpo),
                Paragraph(
                    "Fijación ocular y corporal de la cara orientada al frente." if analisis['atencion_porcentaje'] >= 70
                    else "Atención por debajo del promedio. Alta dispersión visual.", style_cuerpo
                )
            ],
            [
                Paragraph("Frecuencia de Fidgeting / Movimiento", style_cuerpo),
                Paragraph(f"<b>{analisis['fidgeting_score']} / 10</b>", style_cuerpo),
                Paragraph(
                    "Actividad motora dentro del rango basal." if analisis['fidgeting_score'] < 4.0
                    else ("Fidgeting moderado. Movimientos compensatorios constantes." if analisis['fidgeting_score'] < 6.5
                          else "Nivel de hiperactividad física severo. Dificultad para mantener quietud."), style_cuerpo
                )
            ],
            [
                Paragraph("Eventos de Distracción Prolongada", style_cuerpo),
                Paragraph(f"<b>{analisis['eventos_distraccion']} eventos</b>", style_cuerpo),
                Paragraph(f"Pérdidas de atención sostenida de más de 1.5 seg.", style_cuerpo)
            ],
            [
                Paragraph("Tiempo Total de Distracción", style_cuerpo),
                Paragraph(f"<b>{analisis['tiempo_distraccion_seg']} seg</b>", style_cuerpo),
                Paragraph(f"Acumulado fuera del foco de la actividad.", style_cuerpo)
            ]
        ]
        
        t_metricas = Table(datos_metricas, colWidths=[doc.width*0.35, doc.width*0.18, doc.width*0.47])
        t_metricas.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARIO),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [COLOR_FONDO_TABLA, colors.white]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        
        # Sobrescribir colores de textos de cabecera en la tabla para que se lean blancos
        for i in range(3):
            datos_metricas[0][i].style.textColor = colors.white
            
        story.append(t_metricas)
        story.append(Spacer(1, 15))
        
        # ---- GRÁFICO DE LÍNEA DE TIEMPO (Matplotlib insertado en PDF) ----
        try:
            # Recuperar timeline si existe
            timeline = analisis.get("timeline", [])
            grafico_base64 = cls.generar_grafico_timeline(timeline)
            
            # Decodificar Base64 a un buffer de bytes para ReportLab
            img_data = base64.b64decode(grafico_base64)
            img_buffer = io.BytesIO(img_data)
            
            # Insertar en ReportLab desde el buffer de memoria sin escribir en disco
            grafico_flowable = Image(img_buffer, width=7*inch, height=2.8*inch)
            
            story.append(KeepTogether([
                Paragraph("ANÁLISIS DE DINÁMICA DE COMPORTAMIENTO (LÍNEA DE TIEMPO)", style_subtitulo),
                grafico_flowable,
                Spacer(1, 15)
            ]))
        except Exception as e:
            story.append(Paragraph(f"<i>No se pudo insertar el gráfico de línea de tiempo ({str(e)})</i>", style_cuerpo))
            story.append(Spacer(1, 15))
        
        # ---- CONCLUSIONES AUTOMÁTICAS E IMPRESIÓN CLÍNICA ----
        conclusiones_clinicas = [
            Paragraph("<b>IMPRESIONES CLÍNICAS Y CONCLUSIONES AUTOMÁTICAS:</b>", style_subtitulo),
            Paragraph(analisis["diagnostico_auto"], style_conclusion),
            Paragraph("<b>Notas de Evolución Previa de Ficha:</b>", style_cuerpo_bold),
            Paragraph(paciente.get("notes", paciente.get("notas", "Sin notas registradas.")), style_cuerpo),
            Spacer(1, 20)
        ]
        story.append(KeepTogether(conclusiones_clinicas))
        
        # ---- FIRMAS DE VALIDACIÓN ----
        firmas = [
            [
                Paragraph("___________________________________", style_cuerpo),
                Paragraph("___________________________________", style_cuerpo)
            ],
            [
                Paragraph(f"<b>Firma del Especialista:</b><br/>{paciente.get('terapeuta_nombre', 'Terapeuta Asignado')}", style_cuerpo),
                Paragraph("<b>Validación de Dirección Médica:</b><br/>Clínica de Neurodesarrollo e Integración", style_cuerpo)
            ]
        ]
        t_firmas = Table(firmas, colWidths=[doc.width/2.0, doc.width/2.0])
        t_firmas.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(KeepTogether([
            Spacer(1, 20),
            t_firmas
        ]))
        
        # Construir el PDF
        doc.build(story)
            
        return path_salida
