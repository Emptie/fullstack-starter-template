import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import LoadingSpinner from "@/components/LoadingSpinner.vue"

describe("LoadingSpinner", () => {
  it("renders the spinner element", () => {
    const wrapper = mount(LoadingSpinner)
    const spinner = wrapper.find(".animate-spin")
    expect(spinner.exists()).toBe(true)
  })

  it("shows default text when no text prop is provided", () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.text()).toContain("Loading...")
  })

  it("shows custom text when text prop is provided", () => {
    const wrapper = mount(LoadingSpinner, {
      props: { text: "Loading profile..." },
    })
    expect(wrapper.text()).toContain("Loading profile...")
  })

  it("hides text paragraph when text prop is empty string", () => {
    const wrapper = mount(LoadingSpinner, {
      props: { text: "" },
    })
    const paragraphs = wrapper.findAll("p")
    expect(paragraphs.length).toBe(0)
  })
})
