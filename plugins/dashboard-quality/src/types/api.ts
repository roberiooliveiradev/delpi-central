export type ApiSuccessResponse<T> = {
  success: boolean;
  message: string;
  data: T;
};
