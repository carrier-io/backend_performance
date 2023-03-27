const getOrCreateLegendList = (chart, id) => {
    const legendContainer = document.getElementById(id);
    let listContainer = legendContainer.querySelector('div');

    if (!listContainer) {
        listContainer = document.createElement('div');
        listContainer.classList.add('d-grid', 'grid-column-6', 'mt-4');
        legendContainer.appendChild(listContainer);
    }

    return listContainer;
};

const htmlLegendPlugin = {
    id: 'htmlLegend',
    afterUpdate(chart, args, options) {
        const wrapper = getOrCreateLegendList(chart, options.containerID);
        // Remove old legend items
        while (wrapper.firstChild) {
            wrapper.firstChild.remove();
        }

        // Reuse the built-in legendItems generator
        const items = chart.options.plugins.legend.labels.generateLabels(chart);

        items.forEach((item) => {

            const div = document.createElement('div');
            div.classList.add('d-flex', 'mb-3', 'float-left', 'mr-3');

            const label = document.createElement('label');
            label.classList.add('mb-0', 'w-100', 'd-flex', 'align-items-center', 'custom-checkbox', 'custom-checkbox__multicolor', 'legend-item');

            const cbx = document.createElement('input');
            cbx.classList.add('mx-2', 'custom__checkbox');
            cbx.setAttribute('type', 'checkbox');
            cbx.checked = !item.hidden;
            cbx.style.cssText = '--cbx-color:' + item.fillStyle;
            cbx.onchange = () => {
                let hidden = !chart.getDatasetMeta(item.datasetIndex).hidden;
                chart.data.datasets.forEach((ds, i) => {
                    if (chart.getDatasetMeta(item.datasetIndex).label === ds.label) {
                        chart.getDatasetMeta(i).hidden = hidden
                    }
                })
                chart.update()
            }

            const span = document.createElement('span');
            span.classList.add('legend-span');
            span.style.maxWidth = '160px';

            const text = document.createTextNode(item.text);
            span.appendChild(text);

            span.appendChild(text);
            label.appendChild(cbx);
            label.appendChild(span);
            div.appendChild(label);
            wrapper.appendChild(div);
        });
    }
};