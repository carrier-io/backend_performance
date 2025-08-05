# Backend Performance Plugin: Vue Component Integration Guide

This guide describes how to create and integrate new Vue components in the backend_performance plugin, using the user confirmation modals for delete actions as a reference. It is intended for LLM agents and software developers who want to add new features or modals to the plugin.

## 1. Create the Vue Component

- Create a new JS file for your component in `pylon/plugins/backend_performance/static/js/`.
- Use the following structure:

```js
const MyNewModal = {
    delimiters: ['[[', ']]'],
    data() {
        return {
            is_open: false,
            // Add your state variables here
        }
    },
    template: `
        <div class="modal fade" tabindex="-1" role="dialog" id="myNewModal" :class="{show: is_open}" style="display: [[ is_open ? 'block' : 'none' ]]">
            <!-- Modal content here -->
        </div>
    `,
    methods: {
        show(/* args */) {
            // Set state variables
            this.is_open = true;
            $(this.$el).modal('show');
        },
        hide() {
            this.is_open = false;
            $(this.$el).modal('hide');
        },
        confirmAction() {
            // Your action logic
            this.hide();
        }
    }
}
register_component('MyNewModal', MyNewModal);
```

## 2. Add the Component to the Template

- In `pylon/plugins/backend_performance/templates/backend_performance/content.html`, add your modal component:

```html
<My-New-Modal
    @register="register"
    instance_name="my_new_modal"
    modal_id="my_new_modal"
></My-New-Modal>
```

## 3. Invoke the Modal from JS

- In your main JS file (e.g., `backend_performance.js`), invoke the modal using its registered instance name:

```js
if (vueVm.registered_components.my_new_modal) {
    vueVm.registered_components.my_new_modal.show(/* args */);
}
```

## 4. Handle Actions in the Modal

- In the modal's `confirmAction` method, call your backend logic or other functions as needed.
- Pass arguments in the correct format expected by your backend (e.g., comma-separated string for bulk actions).

## 5. Example: User Confirmation for Delete

See `confirm_delete_test.js` for a full example:
- Modal displays confirmation for single or bulk delete.
- Modal receives arrays of IDs/names and displays them.
- On confirm, calls `test_delete(ids.join(','))` to match backend expectations.

## 6. Best Practices

- Always use `delimiters: ['[[', ']]']` for Vue templates in this plugin.
- Register your component with a unique `instance_name`.
- Use consistent modal invocation and registration patterns.
- Ensure your modal's confirm action matches backend API requirements.

## 7. Troubleshooting

- If bulk actions only affect one item, check the format of arguments passed to backend (array vs. string).
- Use the browser console to inspect network requests and debug issues.

---

For further examples, review the files:
- `confirm_delete_test.js`
- `confirm_delete_threshold.js`
- `confirm_delete_result.js`
- `backend_performance.js`
- `content.html`

This guide should help you quickly add new Vue modals and features to the backend_performance plugin.
