package me.shouheng.shuma.utils;

import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author shouh, 2019/3/31-14:11
 */
public class ReflectionUtil {

    private static Map<Class, List<Field>> fieldMap;

    public static List<Field> getAllFields(Object obj) {
        return getAllFields(obj.getClass());
    }

    public static List<Field> getAllFields(Class<?> clz) {
        return getAllFields(clz, FieldsOrder.PARENT_2_CHILDREN);
    }

    public static List<Field> getAllFields(Class<?> clz, FieldsOrder fieldsOrder) {
        if (fieldMap == null) {
            fieldMap = new ConcurrentHashMap<>();
        }
        List<Field> ret = fieldMap.get(clz);
        if (ret != null) {
            return ret;
        }
        ret = new LinkedList<>();
        List<Class> classes = new LinkedList<>();
        while (clz != null) {
            if (fieldsOrder == FieldsOrder.PARENT_2_CHILDREN) {
                // 从父类到子类的顺序添加字段，故父类添加到链表首部
                classes.add(0, clz);
            } else {
                // 父类被添加到链表的尾部
                classes.add(clz);
            }
            clz = clz.getSuperclass();
        }
        for (Class clazz : classes) {
            for (Field f : clazz.getDeclaredFields()) {
                if (!Modifier.isStatic(f.getModifiers())) {
                    ret.add(f);
                }
            }
        }
        return ret;
    }

    public static List<Field> getAllFieldsWithAnnotation(Object obj, Class<? extends Annotation> annotationClass) {
        List<Field> ret = new ArrayList<>();
        for (Field f : getAllFields(obj)) {
            if (f.isAnnotationPresent(annotationClass)) {
                ret.add(f);
            }
        }
        return ret;
    }

    public static boolean hasField(Class<?> cls, String filed) {
        Field[] fields = cls.getDeclaredFields();
        for (Field field : fields) {
            if (field.getName().equals(filed)) {
                return true;
            }
        }
        return false;
    }

    public static boolean getBooleanValue(Class<?> cls, String filed) {
        try {
            return cls.getField(filed).getBoolean(cls.newInstance());
        } catch (IllegalAccessException | NoSuchFieldException | InstantiationException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static String getStringValue(Class<?> cls, String filed) {
        try {
            return (String) cls.getField(filed).get(cls.newInstance());
        } catch (IllegalAccessException | NoSuchFieldException | InstantiationException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static void copy(Object from, Object to) {
        if (from == null || to == null) {
            return;
        }
        try {
            for (Field f : ReflectionUtil.getAllFields(from)) {
                f.setAccessible(true);
                f.set(to, f.get(from));
            }
        } catch (Exception e) {
            throw new RuntimeException("cannot copy members from " + from + " to " + to);
        }
    }

    public static boolean isPrimitiveType(Class<?> clazz) {
        return clazz.isPrimitive()
                || clazz == Byte.class
                || clazz == Short.class
                || clazz == Integer.class
                || clazz == Long.class
                || clazz == Boolean.class
                || clazz == Float.class
                || clazz == Double.class
                || clazz == String.class
                || clazz == Date.class;
    }

    public enum FieldsOrder {
        /**
         * 从子类到父类的顺序
         */
        CHILDREN_2_PARENT,

        /**
         * 从父类到子类的顺序
         */
        PARENT_2_CHILDREN
    }
}
