<script setup lang="ts">
import {ref} from "vue";

const handle = ref("")
const display = ref("")

const handlePrint = (e: Event) => {
  display.value=handle.value
}

</script>

<template>
  <div class="page">
    <div class="container">
      <img src="@/assets/logo.png" alt="logo.png" :class="['logo','container']"/>
      <h1 class="title">CF-Trainer</h1>
    </div>
    <div style="height:25vh;"/>
    <form class="form" @submit.prevent="handlePrint">
      <input v-model="handle" placeholder="Enter handle..."/>
      <button type="submit">Submit</button>
    </form>
    {{display}}
  </div>
</template>

<style scoped>

.page{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.logo{
  max-height: 3.2rem;
  margin: 0 0.4rem;
}

.container {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  height: 15vh;
}

</style>
