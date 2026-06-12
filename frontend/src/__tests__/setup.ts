import { mount } from '@vue/test-utils'
import type { MountingOptions, VueWrapper } from '@vue/test-utils'

/**
 * Minimal Element Plus component stubs for use in component tests.
 *
 * Element Plus components are auto-imported at build time by
 * unplugin-vue-components. In the Vitest/jsdom environment they are
 * not resolved. These stubs provide enough surface area (v-model
 * forwarding, key props, slot rendering) so that component behaviour
 * can be verified without importing the real Element Plus library.
 */
export const EL_STUBS: Record<string, unknown> = {
  'el-badge': {
    template: '<span class="el-badge"><slot /></span>',
    props: ['value', 'hidden', 'max'],
  },
  'el-button': {
    template:
      '<button class="el-button" :disabled="$props.disabled || $props.loading" @click="$emit(\'click\', $event)"><slot /></button>',
    props: ['type', 'size', 'disabled', 'loading', 'plain', 'round', 'circle'],
  },
  'el-dialog': {
    template: '<div v-if="$props.modelValue" class="el-dialog"><slot /></div>',
    props: ['modelValue', 'title', 'width', 'closeOnClickModal'],
    emits: ['update:modelValue'],
  },
  'el-dropdown': {
    template: '<div class="el-dropdown"><slot /><slot name="dropdown" /></div>',
    props: ['trigger'],
  },
  'el-dropdown-item': {
    template: '<div class="el-dropdown-item" @click="$emit(\'click\')"><slot /></div>',
    props: ['divided', 'disabled'],
  },
  'el-dropdown-menu': {
    template: '<div class="el-dropdown-menu"><slot /></div>',
  },
  'el-form': {
    template: '<form class="el-form"><slot /></form>',
    props: ['model', 'labelPosition'],
  },
  'el-form-item': {
    template: '<div class="el-form-item"><slot /></div>',
    props: ['label', 'required', 'prop'],
  },
  'el-icon': {
    template:
      '<i class="el-icon" :style="typeof $props.color === \'string\' ? { color: $props.color } : {}"><slot /></i>',
    props: ['size', 'color'],
  },
  'el-input': {
    template:
      '<input class="el-input" :placeholder="$props.placeholder" :value="$props.modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @keyup.enter="$emit(\'keyup\', $event)" />',
    props: ['modelValue', 'placeholder', 'size', 'clearable', 'showWordLimit', 'maxlength', 'type'],
    emits: ['update:modelValue', 'keyup'],
  },
  'el-menu': {
    template: '<nav class="el-menu"><slot /></nav>',
    props: ['router', 'collapse', 'defaultActive'],
  },
  'el-menu-item': {
    template: '<div class="el-menu-item" @click="$emit(\'click\')"><slot /></div>',
    props: ['index', 'route'],
  },
  'el-option': {
    template: '<option class="el-option" :value="$props.value">{{ $props.label || \'\' }}</option>',
    props: ['value', 'label', 'key'],
  },
  'el-pagination': {
    template:
      '<div class="el-pagination" :data-current-page="$props.currentPage" :data-page-size="$props.pageSize" :data-total="$props.total"><slot /></div>',
    props: ['currentPage', 'pageSize', 'total', 'pageSizes', 'layout', 'background'],
    emits: ['update:currentPage', 'update:pageSize'],
  },
  'el-select': {
    template:
      '<select class="el-select" :value="$props.modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
    props: ['modelValue', 'placeholder', 'filterable'],
    emits: ['update:modelValue'],
  },
  'el-tag': {
    template: '<span class="el-tag" :class="\'el-tag--\' + $props.type"><slot /></span>',
    props: ['type', 'size', 'effect', 'round'],
  },
}

/** Stubs for Vue Router components used in templates. */
export const ROUTER_STUBS = {
  RouterLink: {
    template: '<a class="router-link-stub" :to="$props.to"><slot /></a>',
    props: ['to'],
  },
  RouterView: {
    template: '<div class="router-view-stub"><slot /></div>',
  },
}

/**
 * Mount a component with all standard stubs pre-configured.
 *
 * The caller is still responsible for setting up Pinia before mount:
 *   setActivePinia(createPinia())
 *
 * @param component - The Vue component to mount
 * @param options   - Extra mounting options (merged into global.stubs)
 */
export function mountWithSetup(
  component: unknown,
  options: MountingOptions<Record<string, unknown>> = {},
): VueWrapper {
  return mount(component as never, {
    ...options,
    global: {
      ...options.global,
      stubs: {
        ...EL_STUBS,
        ...ROUTER_STUBS,
        ...(options.global?.stubs as Record<string, unknown>),
      },
    },
  })
}
