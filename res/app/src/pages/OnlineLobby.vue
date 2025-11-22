<template>
    <n-card>
        <strong>{{ t('online.lobbyTitle') }}</strong>
        <div
            style="margin-top: 8px"
            class="muted">
            {{ t('online.notOpen') }}
        </div>
    </n-card>
</template>

<script setup lang="ts">
import { NCard } from "naive-ui";
import { useI18n } from "vue-i18n";
const { t } = useI18n();
</script>
