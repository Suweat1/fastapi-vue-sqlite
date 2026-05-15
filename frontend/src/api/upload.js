import client from './client'

export const uploadImagesApi = async (files) => {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  const { data } = await client.post('/upload/images', formData)
  return data.files
}
