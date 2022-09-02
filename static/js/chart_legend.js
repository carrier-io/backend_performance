const LegendItem = {
    props: [
        'text', 'borderRadius', 'datasetIndex', 'fillStyle', 'fontColor', 'hidden', 'lineCap', 'lineDash',
        'lineDashOffset', 'lineJoin', 'lineWidth', 'strokeStyle', 'pointStyle', 'rotation'
    ],
    template: `
        <div class="d-flex mb-3">
            <label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor">
                <input type="checkbox" class="mx-2 custom__checkbox" 
                    checked="true"
                    id="chart.legend.legendItems[i].datasetIndex"
                     style="--cbx-color: chart.data.datasets[i].backgroundColor;"  
                     onclick="updateChart(event, chart.legend.legendItems[i].datasetIndex)"
                 />
                 <span class="custom-chart-legend-span"></span>
                 chart.data.datasets[i].label
             </label>
         </div>
    `
}
