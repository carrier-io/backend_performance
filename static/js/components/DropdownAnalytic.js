const DropdownAnalytic = {
    props: ['itemsList', 'showAllCbx', 'showSearch', 'instance_name'],
    data() {
        return {
            inputSearch: '',
            refSearchId: 'refSearchCbx'+Math.round(Math.random() * 1000),
            selectedItems: [],
            closeOnItem: true,
            clickedItem: {
                title: '',
                isChecked: false,
            }
        }
    },
    computed: {
        foundItems() {
            return this.inputSearch ?
                this.itemsList.filter(item => {
                    return item.toUpperCase().includes(this.inputSearch.toUpperCase())
                }) :
                this.itemsList
        },
        isAllSelected() {
            return (this.selectedItems.length < this.itemsList.length) && this.selectedItems.length > 0
        }
    },
    watch: {
        selectedItems: function () {
            if(this.showAllCbx) {
                this.$refs[this.refSearchId].checked = this.selectedItems.length === this.itemsList.length ? true : false;
            }
        }
    },
    mounted() {
        $(".dropdown-menu.close-outside").on("click", function (event) {
            event.stopPropagation();
        });
    },
    methods: {
        handlerSelectAll() {
            if (this.selectedItems.length !== this.itemsList.length) {
                this.selectedItems = [...this.itemsList];
            } else {
                this.selectedItems.splice(0);
            }
        },
        setClickedItem(title, e) {
            this.clickedItem = {
                title, isChecked: e.target.checked
            }
            this.$emit('select-items', { selectedItems: this.selectedItems, clickedItem: this.clickedItem});
        }
    },
    template: `
        <div id="complexList" class="complex-list">
            <button class="btn btn-select dropdown-toggle text-left w-100" type="button"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <span v-if="selectedItems.length > 0" 
                    class="complex-list_filled d-inline-block"
                    style="width: calc(100% - 26px);">{{ selectedItems.length }} selected</span>
                    <span v-else class="complex-list_empty d-inline-block" style="width: calc(100% - 26px);">Select</span>
            </button>
            <div class="dropdown-menu close-outside">
                <div v-if="itemsList.length > 4 && showSearch" class="px-3 pb-2 search-group">
                    <div class="custom-input custom-input_search__sm position-relative">
                        <input
                            type="text"
                            placeholder="Search"
                            v-model="inputSearch">
                        <img src="/design-system/static/assets/ico/search.svg" class="icon-search position-absolute">
                    </div>
                </div>
                <ul class="my-0">
                    <li
                       v-if="showAllCbx"
                       class="dropdown-item dropdown-menu_item d-flex align-items-center">
                       <label
                            class="mb-0 w-100 d-flex align-items-center custom-checkbox"
                            :class="{ 'custom-checkbox__minus': isAllSelected }">
                            <input
                                :ref="refSearchId"
                                click="handlerSelectAll"
                                type="checkbox">
                            <span class="w-100 d-inline-block ml-3">All</span>
                       </label>
                    </li>
                    <li
                        class="dropdown-item dropdown-menu_item d-flex align-items-center"
                        v-for="item in foundItems" :key="item">
                         <label
                            class="mb-0 w-100 d-flex align-items-center custom-checkbox">
                            <input
                                :value="item"
                                v-model="selectedItems"
                                @click="setClickedItem(item, $event)"
                                type="checkbox">
                            <span class="w-100 d-inline-block ml-3">{{ item }}</span>
                        </label>
                    </li>
                </ul>
                <div class="p-3" v-if="false">
                    <button class="btn btn-basic mr-2" type="submit">Submit</button>
                    <button type="button" class="btn btn-secondary">Cancel</button>
                </div>
            </div>
        </div>`
};

register_component('dropdown-analytic', DropdownAnalytic);