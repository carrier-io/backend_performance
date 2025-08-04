// Vue component for result delete confirmation modal
const ConfirmDeleteResultModal = {
    delimiters: ['[[', ']]'],
    data() {
        return {
            is_open: false,
            result_ids: [],
            selected_results: [],
        }
    },
    template: `
        <div class="modal fade" tabindex="-1" role="dialog" id="confirmDeleteResultModal" :class="{show: is_open}" style="display: [[ is_open ? 'block' : 'none' ]]">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Delete</h5>
                        <button type="button" class="close" @click="hide" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p v-if="result_ids.length === 1">
                            Are you sure you want to delete the result "<b>[[ selected_results[0]?.name || result_ids[0] ]]</b>"?
                        </p>
                        <p v-else>
                            Are you sure you want to delete <b>[[ result_ids.length ]]</b> results?
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
        show(ids, selected_results = []) {
            this.result_ids = ids;
            this.selected_results = selected_results;
            this.is_open = true;
            $(this.$el).modal('show');
        },
        hide() {
            this.is_open = false;
            $(this.$el).modal('hide');
        },
        confirmDelete() {
            results_delete(this.result_ids.join(','));
            this.hide();
        }
    }
}
register_component('ConfirmDeleteResultModal', ConfirmDeleteResultModal);
