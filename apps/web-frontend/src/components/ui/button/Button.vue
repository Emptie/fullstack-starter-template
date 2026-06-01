<script setup lang="ts">
import { Primitive, type PrimitiveProps } from "reka-ui"
import { computed } from "vue"
import { cn } from "@/lib/utils"

interface Props extends PrimitiveProps {
  variant?: "default" | "destructive" | "outline" | "ghost" | "link"
  size?: "default" | "sm" | "lg" | "icon"
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  as: "button",
  variant: "default",
  size: "default",
})

const classes = computed(() =>
  cn(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
    {
      "bg-primary text-primary-foreground hover:bg-primary/90": props.variant === "default",
      "bg-destructive text-destructive-foreground hover:bg-destructive/90": props.variant === "destructive",
      "border border-input bg-background hover:bg-accent hover:text-accent-foreground": props.variant === "outline",
      "hover:bg-accent hover:text-accent-foreground": props.variant === "ghost",
      "text-primary underline-offset-4 hover:underline": props.variant === "link",
    },
    {
      "h-10 px-4 py-2": props.size === "default",
      "h-9 rounded-md px-3": props.size === "sm",
      "h-11 rounded-md px-8": props.size === "lg",
      "h-10 w-10": props.size === "icon",
    },
    props.class,
  ),
)
</script>

<template>
  <Primitive :as="as" :class="classes">
    <slot />
  </Primitive>
</template>
