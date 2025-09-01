<template>
  <v-app>
    <NavigationBar />
    <v-main class="gradient-background">
      <router-view /> <!-- This displays the current page (e.g., Login, Home, About) -->
    </v-main>
  </v-app>
</template>

<script>
import NavigationBar from '../components/NavigationBar.vue';

export default {
  components: { NavigationBar },
};
</script>

<style scoped>
.gradient-background {
  background: linear-gradient(180deg, 
    #0a0f1c 0%,     /* Very deep navy */
    #0d1421 40%,    /* Deep midnight blue */
    #0f172a 70%,    /* Dark navy */
    #1e293b 90%,    /* Slightly lighter near bottom */
    #334155 97%,    /* Light only at very bottom */
    #475569 100%    /* Lightest at bottom edge */
  );
  min-height: 100vh;
}
</style>