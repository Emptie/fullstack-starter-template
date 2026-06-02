import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import EmptyState from "@/components/EmptyState.vue"

describe("EmptyState", () => {
  it("renders the title", () => {
    const wrapper = mount(EmptyState, {
      props: { title: "No items found" },
    })
    expect(wrapper.text()).toContain("No items found")
  })

  it("renders description when provided", () => {
    const wrapper = mount(EmptyState, {
      props: {
        title: "No items found",
        description: "Try adjusting your filters.",
      },
    })
    expect(wrapper.text()).toContain("Try adjusting your filters.")
  })

  it("does not render description paragraph when description is omitted", () => {
    const wrapper = mount(EmptyState, {
      props: { title: "No items found" },
    })
    const descriptions = wrapper.findAll("p")
    expect(descriptions.length).toBe(0)
  })

  it("renders the SVG icon", () => {
    const wrapper = mount(EmptyState, {
      props: { title: "Empty" },
    })
    const svg = wrapper.find("svg")
    expect(svg.exists()).toBe(true)
  })

  it("renders slot content when provided", () => {
    const wrapper = mount(EmptyState, {
      props: { title: "Nothing here" },
      slots: {
        default: "<button>Take Action</button>",
      },
    })
    expect(wrapper.find("button").exists()).toBe(true)
    expect(wrapper.text()).toContain("Take Action")
  })

  it("does not render slot wrapper when no slot content provided", () => {
    const wrapper = mount(EmptyState, {
      props: { title: "Nothing here" },
    })
    const buttons = wrapper.findAll("button")
    expect(buttons.length).toBe(0)
  })
})
