<template>
  <v-container class="d-flex justify-center align-center fill-height">
    <v-card class="mx-auto" color="indigo">
      <v-card-title class="justify-center">Login</v-card-title>
      <v-card-text>
        <v-form ref="form" v-model="valid" lazy-validation>
          <v-text-field
            v-model="email"
            label="Email"
            type="email"
            :rules="emailRules"
            required
          ></v-text-field>
          <v-text-field
            v-model="password"
            label="Password"
            type="password"
            :rules="passwordRules"
            required
          ></v-text-field>
          <v-btn block color="primary" :disabled="!valid" @click="login">
            Login
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      email: "",
      password: "",
      valid: false,
      emailRules: [
        (v) => !!v || "Email is required",
        (v) => /.+@.+\..+/.test(v) || "E-mail must be valid",
      ],
      passwordRules: [
        (v) => !!v || "Password is required",
        (v) => v.length >= 6 || "Password must be at least 6 characters",
      ],
    };
  },
  methods: {
    login() {
      if (this.$refs.form.validate()) {
        // Handle login logic here
        alert(`Logging in with email: ${this.email}`);
      }
    },
  },
};
</script>

<style scoped>
.fill-height {
  height: 100vh;
}
</style>
