<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12" v-if="started">
        <div class="row g-3">
          <div class="col-6">
            <n-card embedded>
              <n-result status="404" :title="'有游戏吗你就开始'" />
            </n-card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
const started = ref(true);

const gaming = ref({
  height: "100%",
  backgroundColor: "#f5f5f5",
});
</script>
