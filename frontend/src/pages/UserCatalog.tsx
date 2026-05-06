import { Navigate } from 'react-router-dom';

/** Каталог перенесён на страницу профиля → вкладка «История изображений». */
const UserCatalog = () => <Navigate to="/profile?tab=files" replace />;

export default UserCatalog;
