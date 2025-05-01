<template>
  <v-app>
    <NavigationBar />
    <v-main>
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

  