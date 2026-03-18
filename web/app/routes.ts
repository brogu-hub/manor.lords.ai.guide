import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("popout", "routes/popout.tsx"),
  route("api/stream", "routes/api.stream.ts"),
  route("api/*", "routes/api.$.ts"),
] satisfies RouteConfig;
