const BEResultTagsModal = {
    props: ['existedTags', 'servicesTags', 'isLoading', 'isDataLoaded'],
    data() {
        return {
            selectedColor: '#5933c6',
            btt: null,
            selectedTags: [],
            inputText: "",
        }
    },
    computed: {
        isUnCompletedTag() {
            return this.inputText.length;
        },
    },
    watch: {
        isDataLoaded(newValue) {
            if (newValue) {
                this.createColorPicker();
                this.createInputsTags();
            }
        }
    },
    methods: {
        createColorPicker() {
            Coloris({
                el: '#coloris',
                themeMode: 'light',
                onChange: (color) => {
                    this.selectedColor = color;
                    this.btt.changeColor(this.selectedColor)
                },
                swatches: [
                    '#5933c6',
                    '#29B8F5',
                    '#2bd48d',
                    '#EFE482',
                    '#F89033',
                    '#f32626',
                ],
            });
        },
        createInputsTags() {
            this.$nextTick(() => {
                this.btt = BootstrapInputsTags.init("select[multiple]", {
                    onInputChart: (text) => {
                        this.inputText = text;
                    },
                    selectedColor: this.selectedColor,
                });
            })
        },
        handleSubmit() {
            this.selectedTags = this.btt.getFullSelectedValues();
            const sameTags = [];
            const hasServicesTag = this.selectedTags.some(tag => {
                if (this.servicesTags.includes(tag.title)) {
                    sameTags.push(tag.title)
                    return true
                }
                return false;
            });
            if (hasServicesTag) {
               showNotify('ERROR', `Cant use service's name [${sameTags}]`);
               return;
            }
            const uniqueValues = new Set(this.selectedTags.map(v => v.title.toLowerCase()));
            if (uniqueValues.size < this.selectedTags.length) {
                showNotify('ERROR', `Don't use the duplicated name`);
                return;
            }
            this.$emit('update-tags', this.selectedTags);
        },
    },
    template: `
        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <p class="modal-title font-h3" id="exampleModalLabel">Manage Tags</p>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true"><i class="icon__16x16 icon-close__16"></i></span>
                        </button>
                    </div>
                    <div class="modal-body" v-show="btt">
                        <div class="d-flex align-items-center mb-2">
                            <div class="square">
                                <input type="text" id="coloris" class="square" :value="selectedColor">
                            </div>
                            <p class="font-h5 ml-2">Pick color before adding tag</p>
                        </div>
                        <form class="needs-validation form-tags" novalidate onsubmit="event.preventDefault();">
                            <select class="form-select"
                                id="validationTagsShow"
                                name="tags_show[]"
                                multiple
                                data-allow-new="true"
                                data-show-all-suggestions="true"
                                data-allow-clear="true">
                                <option disabled hidden value="">Type to search or create tag</option>
                                <option v-for="tag in existedTags"
                                    :value="tag.title"
                                    :selected="tag.selected"
                                    :data-style-color="tag.hex">{{ tag.title }}</option>
                            </select>
                            <div class="invalid-feedback">Please select a valid tag.</div>
                        </form>
                    </div>
                    <div class="d-flex justify-content-end p-4">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        <button class="btn btn-basic d-flex align-items-center ml-2" 
                            :disabled="isUnCompletedTag"
                            @click="handleSubmit">Save
                            <i v-if="isLoading" class="preview-loader__white ml-2"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
}