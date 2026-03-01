from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush

class ChartsService:
    def __init__(self):
        pass

    def create_best_sellers_chart(self, data):
        """Expects list of (name, quantity) tuples."""
        series = QBarSeries()
        set0 = QBarSet("Quantité Vendue")
        
        categories = []
        for name, qty in data:
            set0.append(qty)
            categories.append(name)
            
        series.append(set0)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Meilleures Ventes (Top 5)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        axisX = QBarCategoryAxis()
        axisX.append(categories)
        axisX.setLabelsBrush(QBrush(Qt.white)) # White text
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        
        axisY = QValueAxis()
        axisY.setLabelsBrush(QBrush(Qt.white)) # White text
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(Qt.white)
        chart.setPlotAreaBackgroundVisible(False)
        chart.legend().setLabelBrush(QBrush(Qt.white)) # White legend text
        
        return chart

    def create_sales_trend_chart(self, data):
        """Expects list of (day, total) tuples."""
        series = QLineSeries()
        series.setColor(Qt.white) # White line
        
        for i, (day, total) in enumerate(data):
            series.append(i, total)
            
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Tendance des Ventes (7 Jours)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(Qt.white)
        
        # Add axes and make them white
        axisX = QValueAxis()
        axisX.setLabelsBrush(QBrush(Qt.white))
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        
        axisY = QValueAxis()
        axisY.setLabelsBrush(QBrush(Qt.white))
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        
        chart.legend().hide()
        
        return chart
