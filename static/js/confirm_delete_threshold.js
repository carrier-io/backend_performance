// Vue component for threshold delete confirmation modal
const ConfirmDeleteThresholdModal = {
    delimiters: ['[[', ']]'],
    data() {
        return {
            is_open: false,
            threshold_ids: [],
            threshold_names: [],
        }
    },
    template: `
        <div class="modal fade" tabindex="-1" role="dialog" id="confirmDeleteThresholdModal" :class="{show: is_open}" style="display: [[ is_open ? 'block' : 'none' ]]">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Delete</h5>
                        <button type="button" class="close" @click="hide" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p v-if="threshold_ids.length === 1">
                            Are you sure you want to delete the threshold "<b>[[ threshold_names[0] || threshold_ids[0] ]]</b>"?
                        </p>
                        <p v-else>
                            Are you sure you want to delete <b>[[ threshold_ids.length ]]</b> thresholds?
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" @click="hide">Cancel</button>
                        <button type="button" class="btn btn-danger" @click="confirmDelete">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        show(ids, names = []) {
            this.threshold_ids = Array.isArray(ids) ? ids : [ids];
            this.threshold_names = Array.isArray(names) ? names : [names];
            this.is_open = true;
            $(this.$el).modal('show');
        },
        hide() {
            this.is_open = false;
            $(this.$el).modal('hide');
        },
        confirmDelete() {
            threshold_delete(this.threshold_ids.join(','));
            this.hide();
        }
    }
}
register_component('ConfirmDeleteThresholdModal', ConfirmDeleteThresholdModal);
