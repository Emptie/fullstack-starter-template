<script setup lang="ts">
import { Label as RekaLabel } from "reka-ui"
import { computed } from "vue"
import { cn } from "@/lib/utils"

interface Props {
  class?: string
  for?: string
}

const props = defineProps<Props>()

const classes = computed(() =>
  cn("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70", props.class),
)
</script>

<template>
  <RekaLabel :class="classes" :for="props.for">
    <slot />
  </RekaLabel>
</template>
